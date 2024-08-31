import os
import re
import json
import sublime
import sublime_plugin
from . import sbot_common as sc


# Definitions.
HIGHLIGHT_FILE_EXT = '.hls'
HIGHLIGHT_SETTINGS_FILE = "SbotHighlight.sublime-settings"

# The internal highlight collections. This is global across all ST instances.
# Key is window id, value is a dict of highlight infos w/key fn.
_hls = {}


#-----------------------------------------------------------------------------------
def plugin_loaded():
    '''Called per plugin instance.'''
    sc.info(f'plugin_loaded() {__package__}')


#-----------------------------------------------------------------------------------
def plugin_unloaded():
    '''Ditto.'''
    pass


#-----------------------------------------------------------------------------------
class HighlightEvent(sublime_plugin.EventListener):

    # Need to track what's been initialized.
    _views_inited = set()
    _store_fn = None

    def on_init(self, views):
        ''' First thing that happens when plugin/window created. Load the persistence file. Views are valid. '''
        settings = sublime.load_settings(HIGHLIGHT_SETTINGS_FILE)

        if len(views) > 0:
            view = views[0]
            w = view.window()
            if w is not None: # view.window() is None here sometimes.
                project_fn = w.project_file_name() 
                self._store_fn = sc.get_store_fn_for_project(project_fn, HIGHLIGHT_FILE_EXT)
                self._open_hls(w)
                for view in views:
                    self._init_view(view)

    def on_load_project(self, window):
        ''' This gets called for new windows but not for the first one. '''
        self._open_hls(window)
        for view in window.views():
            self._init_view(view)

    def on_pre_close_project(self, window):
        ''' Save to file when closing window/project. Seems to be called twice. '''
        # _logger.debug(f'|{window.id()}|{_hls}')
        if window.id() in _hls:
            self._save_hls(window)

    def on_pre_close(self, view):
        w = view.window()
        if w is not None and view.window().id() in _hls:
            self._save_hls(view.window())

    def on_load(self, view):
        ''' Load a file. '''
        self._init_view(view)

    def on_pre_save(self, view):
        w = view.window()
        if w is not None and view.window().id() in _hls:
            self._save_hls(view.window())

    def on_post_save(self, view):
        # Refresh highlights.
        self._highlight_view(view)

    def _init_view(self, view):
        ''' Lazy init. '''
        fn = view.file_name()
        if view.is_scratch() is False and fn is not None:
            # Init the view if not already.
            vid = view.id()
            if vid not in self._views_inited:
                self._views_inited.add(vid)
                self._highlight_view(view)

    def _highlight_view(self, view):
        ''' Colorize the view. '''
        hl_vals = _get_hl_vals(view, False)
        if hl_vals is not None:
            for hl_index, tparams in hl_vals.items():
                _highlight_view(view, tparams['token'], tparams['whole_word'], hl_index)

    def _open_hls(self, window):
        ''' General project opener. '''
        # _logger.debug(f'{self._store_fn}')
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
        # _logger.debug(f'{self._store_fn}')
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
    ''' Highlight specific words using scopes. Parts borrowed from StyleToken. '''

    def run(self, edit, hl_index):
        # Get whole word or specific span.
        region = self.view.sel()[0]

        whole_word = region.empty()
        if whole_word:
            region = self.view.word(region)
        token = self.view.substr(region)

        hl_vals = _get_hl_vals(self.view, True)
        if hl_vals is not None:
            hl_vals[hl_index] = {"token": token, "whole_word": whole_word}
        _highlight_view(self.view, token, whole_word, hl_index)


#-----------------------------------------------------------------------------------
class SbotClearHighlightsCommand(sublime_plugin.TextCommand):
    ''' Clear all in this file.'''

    def run(self, edit):
        # Clear visuals in open views.
        hl_info = sc.get_highlight_info('user')
        for hl in hl_info:
            self.view.erase_regions(hl.region_name)

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
        # Clear visuals in open views.
        hl_info = sc.get_highlight_info('user')
        for vv in self.view.window().views():
            for hl in hl_info:
                self.view.erase_regions(hl.region_name)

        # Clear collection for current window only.
        winid = self.view.window().id()
        if winid in _hls:
            _hls[winid] = {}


#-----------------------------------------------------------------------------------
class SbotAllScopesCommand(sublime_plugin.TextCommand):
    ''' Show style info for common scopes. '''

    def run(self, edit):
        settings = sublime.load_settings(HIGHLIGHT_SETTINGS_FILE)
        scopes = settings.get('scopes_to_show')
        _render_scopes(scopes, self.view)


#-----------------------------------------------------------------------------------
class SbotScopeInfoCommand(sublime_plugin.TextCommand):
    ''' Like builtin ShowScopeNameCommand but with coloring added. '''

    def run(self, edit):
        caret = sc.get_single_caret(self.view)
        if caret is not None:
            scope = self.view.scope_name(caret).rstrip()
            scopes = scope.split()
            _render_scopes(scopes, self.view)


#-----------------------------------------------------------------------------------
def _highlight_view(view, token, whole_word, hl_index):
    ''' Colorize one token. '''
    escaped = re.escape(token)
    if whole_word:  # and escaped[0].isalnum():
        escaped = r'\b%s\b' % escaped

    # json uses string keys so convert to int.
    hl_index = int(hl_index)
    hl_info = sc.get_highlight_info('user')

    if hl_index < len(hl_info):
        highlight_regions = view.find_all(escaped) if whole_word else view.find_all(token, sublime.LITERAL)
        if len(highlight_regions) > 0:
            hl = hl_info[hl_index]
            view.add_regions(hl.region_name, highlight_regions, hl.scope_name)
    else:
        sc.warn(f'Invalid scope index {hl_index}')


#-----------------------------------------------------------------------------------
def _get_hl_vals(view, init_empty):
    ''' General helper to get the data values from persisted collection. If init_empty and there are none, add a default value. '''
    vals = None  # Default
    winid = view.window().id()
    fn = view.file_name()

    if winid not in _hls and init_empty:
        # Add a new one.
        _hls[winid] = {}

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
def _render_scopes(scopes, view):
    ''' Make popup for list of scopes. '''

    style_text = []
    content = []

    for scope in scopes:
        style = view.style_for_scope(scope)
        props = f'{{ color:{style["foreground"]}; '
        props2 = f'fg:{style["foreground"]} '
        if 'background' in style:
            props += f'background-color:{style["background"]}; '
            props2 += f'bg:{style["background"]} '
        if style['bold']:
            props += 'font-weight:bold; '
            props2 += 'bold '
        if style['italic']:
            props += 'font-style:italic; '
            props2 += 'italic '
        props += '}'

        i = len(style_text)
        style_text.append(f'.st{i} {props}')
        content.append(f'<p><span class=st{i}>{scope}  {props2}</span></p>')

    # Do popup
    st = '\n'.join(style_text)
    ct = '\n'.join(content)

    html = f'''
<body>
<style> p {{ margin: 0em; }} {st} </style>
{ct}
</body>
<a href="_copy_scopes">Copy</a>
'''

    to_show = '\n'.join(scopes)
    # to_show = html
    view.show_popup(html, max_width=512, max_height=600, on_navigate=lambda x: _copy_scopes(view, to_show))


#-----------------------------------------------------------------------------------
def _copy_scopes(view, scopes):
    ''' Copy to clipboard. '''

    sublime.set_clipboard(scopes)
    view.hide_popup()
    sublime.status_message('Scope names copied to clipboard')
