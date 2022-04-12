import os
import re
import pathlib
import json
import sublime
import sublime_plugin


# Definitions.
HIGHLIGHT_REGION_NAME = 'highlight_%s'
HIGHLIGHT_FILE_EXT = '.sbot-hls'

# The current highlight collections. This is global across all ST instances/window/project.
# Key is current window id, value is the collection of file/highlight info.
_hls = {}


#-----------------------------------------------------------------------------------
# Decorator for tracing function entry.
def trace_func(func):
    def inner(ref, *args):
        print(f'FUN {ref.__class__.__name__}.{func.__name__} {args}')
        return func(ref, *args)
    return inner


#-----------------------------------------------------------------------------------
class HighlightEvent(sublime_plugin.EventListener):

    # Need to track what's been initialized.
    views_inited = set()

    @trace_func
    def on_init(self, views):
        ''' First thing that happens when plugin/window created. Load the persistence file. Views are valid. '''
        view = views[0]
        self._open_hls(view.window().id(), view.window().project_file_name())
        for view in views:
            self._init_view(view)

    @trace_func
    def on_load_project(self, window):
        ''' This gets called for new windows but not for the first one. '''
        self._open_hls(window.id(), window.project_file_name())
        # print(f'### wid:{window.id()} proj:{window.project_file_name()} _hls:{_hls}')
        for view in window.views():
            self._init_view(view)

    @trace_func
    def on_pre_close_project(self, window):
        ''' Save to file when closing window/project. Seems to be called twice. '''
        # print(f'### wid:{window.id()} _hls:{_hls}')
        winid = window.id()
        if winid in _hls:
            self._save_hls(winid, window.project_file_name())

    @trace_func
    def on_load(self, view):
        ''' Load a file. '''
        self._init_view(view)

    @trace_func
    def _init_view(self, view):
        ''' Lazy init. '''
        fn = view.file_name()
        if view.is_scratch() is False and fn is not None:
            # Init the view if not already.
            vid = view.id()
            if vid not in self.views_inited:
                self.views_inited.add(vid)

                # Init the view with any persist values.
                tokens = _get_persist_tokens(view, False)
                if tokens is not None:
                    for token, tparams in tokens.items():
                        _highlight_view(view, token, tparams['whole_word'], tparams['scope'])

    @trace_func
    def _open_hls(self, winid, project_fn):
        ''' General project opener. '''
        global _hls
        
        if project_fn is not None:
            store_fn = _get_store_fn(project_fn)

            if os.path.isfile(store_fn):
                with open(store_fn, 'r') as fp:
                    values = json.load(fp)
                    _hls[winid] = values
            else:
                # Assumes new file.
                sublime.status_message('Creating new highlights file')
                _hls[winid] = {}

    @trace_func
    def _save_hls(self, winid, project_fn):
        ''' General project saver. '''
        global _hls

        if project_fn is not None:
            store_fn = _get_store_fn(project_fn)

            # Remove invalid files and any empty values.
            # Safe iteration - accumulate elements to del later.
            del_els = []

            for fn, _ in _hls[winid].items():
                if fn is not None:
                    if not os.path.exists(fn):
                        del_els.append((winid, fn))
                    elif len(_hls[winid][fn]) == 0:
                        del_els.append((winid, fn))

            # Now remove from collection.
            for (w, fn) in del_els:
                del _hls[w][fn]

            # Now save, or delete if empty.
            if len(_hls[winid]) > 0:
                with open(store_fn, 'w') as fp:
                    json.dump(_hls[winid], fp, indent=4)
            elif os.path.isfile(store_fn):
                os.remove(store_fn)


#-----------------------------------------------------------------------------------
class SbotHighlightTextCommand(sublime_plugin.TextCommand):
    ''' Highlight specific words using scopes. Parts borrowed from StyleToken.
    Note: Regions added by self.view.add_regions() can not set the foreground color. The scope color is used
    for the region background color. Also they are not available via extract_scope().
    '''

    def run(self, edit, hl_index):
        settings = sublime.load_settings("SbotHighlight.sublime-settings")
        highlight_scopes = settings.get('highlight_scopes')

        # Get whole word or specific span.
        region = self.view.sel()[0]

        whole_word = region.empty()
        if whole_word:
            region = self.view.word(region)
        token = self.view.substr(region)

        hl_index %= len(highlight_scopes)
        scope = highlight_scopes[hl_index]
        tokens = _get_persist_tokens(self.view, True)

        if tokens is not None:
            tokens[token] = {"scope": scope, "whole_word": whole_word}
        _highlight_view(self.view, token, whole_word, scope)


#-----------------------------------------------------------------------------------
class SbotClearHighlightsCommand(sublime_plugin.TextCommand):
    ''' Clear all in this file.'''

    def run(self, edit):
        global _hls

        # Clear visuals in open views.
        settings = sublime.load_settings("SbotHighlight.sublime-settings")
        highlight_scopes = settings.get('highlight_scopes')

        for i, value in enumerate(highlight_scopes):
            reg_name = HIGHLIGHT_REGION_NAME % value
            self.view.erase_regions(reg_name)

        # Remove from persist collection.
        winid = self.view.window().id()
        if winid in _hls:
            fn = self.view.file_name()
            del _hls[winid][fn]


#-----------------------------------------------------------------------------------
class SbotClearAllHighlightsCommand(sublime_plugin.TextCommand):
    ''' Clear all in this project.'''

    def run(self, edit):
        global _hls

        # Clear visuals in open views.
        settings = sublime.load_settings("SbotHighlight.sublime-settings")
        highlight_scopes = settings.get('highlight_scopes')

        for vv in self.view.window().views():
            for i, value in enumerate(highlight_scopes):
                reg_name = HIGHLIGHT_REGION_NAME % value
                vv.erase_regions(reg_name)

        # Clear collection for current window only.
        winid = self.view.window().id()
        if winid in _hls:
            _hls[winid] = {}


#-----------------------------------------------------------------------------------
def _highlight_view(view, token, whole_word, scope):
    ''' Colorize one token. '''

    escaped = re.escape(token)
    if whole_word and escaped[0].isalnum():
        escaped = r'\b%s\b' % escaped

    highlight_regions = view.find_all(escaped) if whole_word else view.find_all(token, sublime.LITERAL)
    if len(highlight_regions) > 0:
        view.add_regions(HIGHLIGHT_REGION_NAME % scope, highlight_regions, scope)


#-----------------------------------------------------------------------------------
def _get_persist_tokens(view, init_empty):
    ''' General helper to get the data values from collection. If init_empty and there are none, add a default value. '''
    global _hls
    
    vals = None  # Default
    winid = view.window().id()
    fn = view.file_name()

    if winid in _hls:
        if fn not in _hls[winid]:
            if init_empty:
                # Add a new one.
                _hls[winid][fn] = {}
                vals = _hls[winid][fn]
        else:
            vals = _hls[winid][fn]

    return vals

#-----------------------------------------------------------------------------------
def _get_store_fn(project_fn):
    ''' General utility. '''

    store_path = os.path.join(sublime.packages_path(), 'User', 'SbotStore')
    pathlib.Path(store_path).mkdir(parents=True, exist_ok=True)
    project_fn = os.path.basename(project_fn).replace('.sublime-project', HIGHLIGHT_FILE_EXT)
    store_fn = os.path.join(store_path, project_fn)
    return store_fn
