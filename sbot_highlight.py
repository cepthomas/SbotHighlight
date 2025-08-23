import sys
import os
import re
import json
import sublime
import sublime_plugin
from . import sbot_common as sc


# The current highlights. This is global across all ST instances/window/projects.
_hls = {}
# {
#     "my.sublime-project": {
#         "file_with_signets_1.ext": {
#             "0": { "token": "crows", "whole_word": false },
#             "1": { "token": "drows", "whole_word": false },
#         },
#         "file_with_signets_1.ext":
#         ...
#     },
#     "project file2":
#     ...
# }



# Predefined scopes to display.
_notr_scopes = [
    "text.notr", "markup.bold.notr", "markup.directive.notr", "markup.heading.content.notr", "markup.heading.notr", 
    "markup.heading.tags.notr", "markup.hrule.notr", "markup.italic.notr", "markup.link.name.notr", 
    "markup.link.refname.notr", "markup.link.tags.notr", "markup.link.target.notr", "markup.list.indent.notr", 
    "markup.list.marker.dash.notr", "markup.list.marker.exclmation.notr", "markup.list.marker.plus.notr", 
    "markup.list.marker.question.notr", "markup.list.marker.x.notr", "markup.quote.notr", 
    "markup.raw.block.notr", "markup.raw.inline.notr", "markup.strikethrough.notr", "markup.underline.notr", 
    "punctuation.definition.block.begin.notr", "punctuation.definition.block.end.notr",
]

_internal_scopes = [
    "markup.user_hl1", "markup.user_hl2", "markup.user_hl3", "markup.user_hl4", "markup.user_hl5",
    "markup.user_hl6", "markup.fixed_hl1", "markup.fixed_hl2", "markup.fixed_hl3",
]

_markup_scopes = [
    "markup", "markup.underline", "markup.underline.link",
    "markup.italic", "markup.bold", "markup.strikethrough",
    "markup.heading", "markup.paragraph", "markup.quote", "markup.list", 
    "markup.inserted.diff", "markup.deleted.diff",
    "meta.table", "meta.table.header", "meta.link.reference",
]

_syntax_scopes = [
    "comment", "comment.block", "comment.block.documentation",
    "constant", "entity", "entity.name", "entity.name.section", "invalid", 
    "keyword", "keyword.control", "keyword.declaration", "keyword.operator",
    "variable", "variable.function", "variable.language", "variable.parameter",
    "storage", "storage.modifier", "storage.type",
    "string", "string.quoted.single", "string.quoted.double",
    "text", "text.documentation",
]

_generic_colors_scopes = [
    "region.redish", "region.orangish", "region.yellowish", "region.greenish", "region.cyanish",
    "region.bluish", "region.purplish", "region.pinkish",
]


#-----------------------------------------------------------------------------------
def plugin_loaded():
    '''Called per plugin instance.'''
    pass


#-----------------------------------------------------------------------------------
class HighlightEvent(sublime_plugin.EventListener):
    ''' React to system events.'''

    # Track what's been initialized.
    _views_inited = set()

    def on_init(self, views):
        ''' First thing that happens when plugin/window created. Load the persistence file. Views are valid. '''
        if len(views) > 0:
            view = views[0]
            win = view.window()
            if win is not None:
                project_fn = win.project_file_name()
                self._read_store()
                for view in views:
                    self._init_view(view)

    def on_load_project(self, window):
        ''' This gets called for new windows but not for the first one. '''
        for view in window.views():
            self._init_view(view)

    def on_pre_close_project(self, window):
        ''' Save to file when closing window/project. '''
        self._write_store()

    def on_load(self, view):
        ''' Load a file. '''
        self._init_view(view)

    def on_post_save(self, view):
        ''' Save a file, refresh. '''
        self._highlight_view(view)

    def _init_view(self, view):
        ''' Lazy init. '''
        fn = view.file_name()
        if view.is_scratch() is True or fn is None:
            return

        project_hls = _get_project_hls(view, init=False)
        if project_hls is None:
            return

        # Init the view if not already.
        vid = view.id()
        if vid not in self._views_inited:
            self._views_inited.add(vid)
            self._highlight_view(view)

    def _read_store(self):
        ''' General project opener. '''
        global _hls

        store_fn = sc.get_store_fn()
        if os.path.isfile(store_fn):
            try:
                with open(store_fn, 'r') as fp:
                    _temp_hls = json.load(fp)
                    # Sanity checks. Easier to make a new clean collection rather than remove parts.
                    _hls.clear()

                    for proj_fn, proj_hls in _temp_hls.items():
                        if os.path.exists(proj_fn) and len(proj_hls) > 0:
                            files = {}
                            for fn, hls in proj_hls.items():
                                if os.path.exists(fn) and len(hls) > 0:
                                    files[fn] = hls
                            if len(files) > 0:
                                _hls[proj_fn] = files
            except Exception as e:
                sc.error(f'Error reading {store_fn}: {e}', e.__traceback__)
        else:  # Assume new file with default fields.
            sublime.status_message('Creating new highlights file')
            _hls = {}

    def _write_store(self):
        ''' General project saver. '''
        global _hls

        store_fn = sc.get_store_fn()

        try:
            with open(store_fn, 'w') as fp:
                json.dump(_hls, fp, indent=4)
        except Exception as e:
            sc.error(f'Error writing {store_fn}: {e}', e.__traceback__)

    def _highlight_view(self, view):
        ''' Colorize the view. '''
        hl_vals = _get_hl_vals(view, init=False)
        if hl_vals is not None:
            for hl_index, tparams in hl_vals.items():
                _highlight_view(view, tparams['token'], tparams['whole_word'], hl_index)


#-----------------------------------------------------------------------------------
class SbotHighlightTextCommand(sublime_plugin.TextCommand):
    ''' Highlight specific words using scopes. Parts borrowed from StyleToken. '''

    def run(self, edit, hl_index):
        del edit
        # Get whole word or specific span.
        region = self.view.sel()[0]

        whole_word = region.empty()
        if whole_word:
            region = self.view.word(region)
        token = self.view.substr(region)

        hl_vals = _get_hl_vals(self.view, init=True)
        if hl_vals is not None:
            hl_vals[hl_index] = {"token": token, "whole_word": whole_word}
        _highlight_view(self.view, token, whole_word, hl_index)


#-----------------------------------------------------------------------------------
class SbotClearHighlightsCommand(sublime_plugin.TextCommand):
    ''' Clear all in this file.'''

    def is_visible(self):
        # Don't allow signets in temp views.
        return self.view.is_scratch() is False and self.view.file_name() is not None

    def run(self, edit):
        del edit

        view = self.view
        win = view.window()
        fn = view.file_name()

        project_hls = _get_project_hls(view, init=False)
        if project_hls is None:
            return  # --- early return

        # Don't allow signets in temp views.
        if view.is_scratch() is True or fn is None:
            return

        for file, hls in project_hls.items():
            if file == fn:
                # Remove from persist collection.
                del project_hls[fn]

                # Clear visuals in view.
                hl_info = sc.get_highlight_info('user')
                for hl in hl_info:
                    view.erase_regions(hl.region_name)

                break


#-----------------------------------------------------------------------------------
class SbotClearAllHighlightsCommand(sublime_plugin.TextCommand):
    ''' Clear all in this project.'''

    def run(self, edit):
        del edit
        win = self.view.window()

        project_hls = _get_project_hls(self.view, init=False)
        if project_hls is None:
            return  # --- early return

        # Bam.
        try:
            del _hls[self.view.window().project_file_name()]  # pyright: ignore
        # except Exception as e:
        #     pass
        finally:
            # Clear visuals in open views.
            hl_info = sc.get_highlight_info('user')
            for _ in win.views():  # pyright: ignore
                for hl in hl_info:
                    self.view.erase_regions(hl.region_name)


#-----------------------------------------------------------------------------------
class SbotAllScopesCommand(sublime_plugin.TextCommand):
    ''' Show style info for common scopes. '''

    def run(self, edit):
        del edit
        scopes = []

        if (self.view.file_name() is not None and self.view.syntax() is not None and self.view.syntax().name == 'Notr'):
            scopes.extend(_notr_scopes)
        scopes.extend(_markup_scopes)
        scopes.extend(_internal_scopes)
        scopes.extend(_syntax_scopes)
        scopes.extend(_generic_colors_scopes)
        # User requests?
        settings = sublime.load_settings(sc.get_settings_fn())
        extra_scopes = settings.get('scopes_to_show')
        scopes.extend(extra_scopes)  # pyright: ignore

        _render_scopes(scopes, self.view)

#-----------------------------------------------------------------------------------
class SbotScopeInfoCommand(sublime_plugin.TextCommand):
    ''' Like builtin ShowScopeNameCommand but with coloring added. '''

    def run(self, edit):
        del edit
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
        sc.error(f'Invalid scope index {hl_index}')


#-----------------------------------------------------------------------------------
def _get_hl_vals(view, init):
    ''' General helper to get the data values from persisted collection. If init and there are none, add a default value. '''
    vals = None
    win = view.window()
    fn = view.file_name()

    project_hls = _get_project_hls(view, init=True)

    if project_hls is not None:
        if fn not in project_hls:
            if init:
                # Add a new one.
                project_hls[fn] = {}
                vals = project_hls[fn]
        else:
            vals = project_hls[fn]

    return vals


#-----------------------------------------------------------------------------------
def _get_project_hls(view, init=True):
    ''' Get the signets associated with this view or None. Option to create a new entry if missing.'''
    hls = None
    win = view.window()
    if win is not None:
        project_fn = win.project_file_name()
        if project_fn not in _hls:
            if init:
                _hls[project_fn] = {}
                hls = _hls[project_fn]
        else:
            hls = _hls[project_fn]
    return hls


#-----------------------------------------------------------------------------------
def _render_scopes(scopes, view):
    ''' Make popup for list of scopes. '''
    style_text = []
    content = []
    short_content = []

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
        short_content.append(f'{scope}  {props2}')

    # Do popup
    st = '\n'.join(style_text)
    ct = '\n'.join(content)
    sc = '\n'.join(short_content)

    # Html for popup.
    html = f'''
<body>
<style> p {{ margin: 0em; }} {st} </style>
{ct}
</body>
<a href="copy_scopes">Copy To Clipboard</a>
'''

    to_show = '\n'.join(scopes)

    # Callback
    def nav(href):
        ''' Copy to clipboard. '''
        to_html = f'''
<body>
<style> p {{ margin: 0em; }} {st} </style>
{ct}
</body>
'''

        # sublime.set_clipboard(to_html)
        # sublime.set_clipboard(to_show)
        sublime.set_clipboard(sc)
        view.hide_popup()
        sublime.status_message('Scopes copied to clipboard')

    view.show_popup(html, max_width=512, max_height=600, on_navigate=nav)
