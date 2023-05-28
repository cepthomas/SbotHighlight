import os
import re
import json
import sublime
import sublime_plugin
from . import sbot_common as sc


# Definitions.
HIGHLIGHT_FILE_EXT = '.sbot-hls'
HIGHLIGHT_SETTINGS_FILE = "SbotHighlight.sublime-settings"


# The current highlight collections. This is global across all ST instances/window/project.
# Key is current window id, value is the collection of file/highlight info.
_hls = {}

# TODO refresh_hls cmd instead of closing/opening the view.


#-----------------------------------------------------------------------------------
class HighlightEvent(sublime_plugin.EventListener):

    # Need to track what's been initialized.
    _views_inited = set()
    _store_fn = None

    def on_init(self, views):
        ''' First thing that happens when plugin/window created. Load the persistence file. Views are valid. '''
        view = views[0]
        settings = sublime.load_settings(HIGHLIGHT_SETTINGS_FILE)
        project_fn = view.window().project_file_name()
        self._store_fn = sc.get_store_fn_for_project(project_fn, HIGHLIGHT_FILE_EXT)
        self._open_hls(view.window())
        for view in views:
            self._init_view(view)

    def on_load_project(self, window):
        ''' This gets called for new windows but not for the first one. '''
        self._open_hls(window)
        for view in window.views():
            self._init_view(view)

    def on_pre_close_project(self, window):
        ''' Save to file when closing window/project. Seems to be called twice. '''
        # slog(CAT_DBG, f'|{window.id()}|{_hls}')
        if window.id() in _hls:
            self._save_hls(window)

    def on_pre_close(self, view):
        w = view.window()
        if w is not None and view.window().id() in _hls:
            self._save_hls(view.window())

    def on_load(self, view):
        ''' Load a file. '''
        self._init_view(view)

    def _init_view(self, view):
        ''' Lazy init. '''
        fn = view.file_name()
        if view.is_scratch() is False and fn is not None:
            # Init the view if not already.
            vid = view.id()
            if vid not in self._views_inited:
                self._views_inited.add(vid)

                # Init the view with any persist values.
                hl_vals = _get_hl_vals(view, False)
                if hl_vals is not None:
                    for scope, tparams in hl_vals.items():
                        _highlight_view(view, tparams['token'], tparams['whole_word'], scope)

    def _open_hls(self, window):
        ''' General project opener. '''
        # slog(CAT_DBG, f'{self._store_fn}')
        global _hls

        if self._store_fn is not None:
            winid = window.id()

            if os.path.isfile(self._store_fn):
                with open(self._store_fn, 'r') as fp:
                    values = json.load(fp)
                    _hls[winid] = values
            else:
                # Assumes new file.
                sublime.status_message('Creating new highlights file')
                _hls[winid] = {}

    def _save_hls(self, window):
        ''' General project saver. '''
        # slog(CAT_DBG, f'{self._store_fn}')
        global _hls

        if self._store_fn is not None:
            winid = window.id()

            # Remove invalid files and any empty values.
            # Safe iteration - accumulate elements to del later.
            del_els = []

            hls = _hls[winid]

            for fn, _ in hls.items():
                if fn is not None:
                    if not os.path.exists(fn):
                        del_els.append((winid, fn))
                    elif len(hls[fn]) == 0:
                        del_els.append((winid, fn))

            # Now remove from collection.
            for (w, fn) in del_els:
                del _hls[w][fn]

            # Now save, or delete if empty.
            if len(hls) > 0:
                with open(self._store_fn, 'w') as fp:
                    json.dump(hls, fp, indent=4)
            elif os.path.isfile(self._store_fn):
                os.remove(self._store_fn)


#-----------------------------------------------------------------------------------
class SbotHighlightTextCommand(sublime_plugin.TextCommand):
    ''' Highlight specific words using scopes. Parts borrowed from StyleToken.
    Note: Regions added by self.view.add_regions() can not set the foreground color. The scope color is used
    for the region background color. Also they are not available via extract_scope().
    '''

    def run(self, edit, hl_index):
        settings = sublime.load_settings(HIGHLIGHT_SETTINGS_FILE)
        highlight_scopes = settings.get('highlight_scopes')

        # Get whole word or specific span.
        region = self.view.sel()[0]

        whole_word = region.empty()
        if whole_word:
            region = self.view.word(region)
        token = self.view.substr(region)

        hl_index %= len(highlight_scopes)
        scope = highlight_scopes[hl_index]
        hl_vals = _get_hl_vals(self.view, True)

        if hl_vals is not None:
            hl_vals[scope] = {"token": token, "whole_word": whole_word}
        _highlight_view(self.view, token, whole_word, scope)


#-----------------------------------------------------------------------------------
class SbotClearHighlightsCommand(sublime_plugin.TextCommand):
    ''' Clear all in this file.'''

    def run(self, edit):
        global _hls

        # Clear visuals in open views.
        settings = sublime.load_settings(HIGHLIGHT_SETTINGS_FILE)
        highlight_scopes = settings.get('highlight_scopes')

        for i, value in enumerate(highlight_scopes):
            reg_name = sc.HIGHLIGHT_REGION_NAME % value
            self.view.erase_regions(reg_name)

        # Remove from persist collection.
        winid = self.view.window().id()
        if winid in _hls:
            fn = self.view.file_name()
            if fn is not None and fn in _hls[winid]:
                del _hls[winid][fn]


#-----------------------------------------------------------------------------------
class SbotClearAllHighlightsCommand(sublime_plugin.TextCommand):
    ''' Clear all in this project.'''

    def run(self, edit):
        global _hls

        # Clear visuals in open views.
        settings = sublime.load_settings(HIGHLIGHT_SETTINGS_FILE)
        highlight_scopes = settings.get('highlight_scopes')

        for vv in self.view.window().views():
            for i, value in enumerate(highlight_scopes):
                reg_name = sc.HIGHLIGHT_REGION_NAME % value
                vv.erase_regions(reg_name)

        # Clear collection for current window only.
        winid = self.view.window().id()
        if winid in _hls:
            _hls[winid] = {}


#-----------------------------------------------------------------------------------
def _highlight_view(view, token, whole_word, scope):
    ''' Colorize one token. '''
    escaped = re.escape(token)
    if whole_word:  # and escaped[0].isalnum():
        escaped = r'\b%s\b' % escaped

    highlight_regions = view.find_all(escaped) if whole_word else view.find_all(token, sublime.LITERAL)
    if len(highlight_regions) > 0:
        view.add_regions(sc.HIGHLIGHT_REGION_NAME % scope, highlight_regions, scope)


#-----------------------------------------------------------------------------------
def _get_hl_vals(view, init_empty):
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
