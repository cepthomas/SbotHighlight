import os
import re
import pathlib
import json
import sublime
import sublime_plugin

# TODO clear all hls in project.

# Definitions.
HIGHLIGHT_REGION_NAME = 'highlight_%s'
HIGHLIGHT_FILE_EXT = '.sbot-hls'

# The current highlight collections. Key is window id which corresponds to a project.
_hls = None

# Need to track what's been initialized.
_views_inited = set()

# Where we keep the persistence.
_store_path = None


#-----------------------------------------------------------------------------------
class HighlightEvent(sublime_plugin.EventListener):

    def on_init(self, views):
        ''' First thing that happens. '''

        # Init now.
        global _store_path
        _store_path = os.path.join(sublime.packages_path(), 'User', 'SbotStore')
        pathlib.Path(_store_path).mkdir(parents=True, exist_ok=True)

        view = views[0]
        _open_hls(view.window().id(), view.window().project_file_name())

    def on_load(self, view):
        ''' When you load an existing file. '''
        global _views_inited

        vid = view.id()
        # winid = view.window().id()
        fn = view.file_name()

        # Lazy init.
        if fn is not None:  # Sometimes this happens...
            # Init the view if not already.
            if vid not in _views_inited:
                _views_inited.add(vid)

                # Init the view with any persist values.
                tokens = _get_persist_tokens(view, False)
                if tokens is not None:
                    for token, tparams in tokens.items():
                        _highlight_view(view, token, tparams['whole_word'], tparams['scope'])

    def on_deactivated(self, view):
        ''' Save to file when focus/tab lost. '''
        if _hls is not None:
            winid = view.window().id()
            if winid in _hls:
                _save_hls(winid, view.window().project_file_name())


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

        # Clean displayed colors.
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
def _get_store_fn(project_fn):
    ''' General utility. '''
    global _store_path
    project_fn = os.path.basename(project_fn).replace('.sublime-project', HIGHLIGHT_FILE_EXT)
    store_fn = os.path.join(_store_path, project_fn)
    return store_fn


#-----------------------------------------------------------------------------------
def _save_hls(winid, project_fn):
    ''' General project saver. '''

    if project_fn is not None:
        store_fn = _get_store_fn(project_fn)

        # Remove invalid files and any empty values.
        if winid in _hls:
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
def _open_hls(winid, project_fn):
    ''' General project opener. '''

    global _hls
    _hls = {}
    
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

    if _hls is not None:
        if winid in _hls:
            if fn not in _hls[winid]:
                if init_empty:
                    # Add a new one.
                    _hls[winid][fn] = {}
                    vals = _hls[winid][fn]
            else:
                vals = _hls[winid][fn]

    return vals
