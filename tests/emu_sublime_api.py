import os
import sys
import json
import time
import datetime
import string

'''
A simple emulation of the ST api solely for the purpose of debugging plugins.
This enables the use of standard components like unittest without using
the ST embedded python. Any local flavor of python >= 3.8 should work fine.

Primarily intended for testing on Windows but should be easy to tweak for nx flavors
by replacing instances of APPDATA with platform variants.

Some actions don't lend themselves easily to this simple model, usually raises
NotImplementedError. For those MagicMock is likely a better choice.

Conforms partly to https://www.sublimetext.com/docs/api_reference.html.
Missing items throw NotImplementedError.

All internal row/column are 0-based. Client is responsible for converting for UI 1-based.
Position is always 0-based.

Some guessing as to how ST validates args - seems to be clamping not throwing.
'''

#---------- Replace sublime api -----------

# Get a reference to myself. Seems like it shouldn't work but, python...
import emu_sublime_api

# Add path to code under test - assumed it's the parent dir.
_cut_path = os.path.join(os.path.dirname(__file__), '..')
if _cut_path not in sys.path:
    sys.path.insert(0, _cut_path)

# Thunk the system modules so code under test sees this emulation rather than the real libs.
sys.modules["sublime"] = emu_sublime_api
sys.modules["sublime_plugin"] = emu_sublime_api


#--------- Internal states -------------------

_active_window = None
_next_id = 1
_settings = None
_clipboard = ''

TEST_OUT_PATH = os.path.join(os.path.dirname(__file__), 'out')

#--------- Internal utilities -------------------

def _write_trace(cat, s):
    with open(os.path.join(TEST_OUT_PATH, 'trace.txt'), 'a') as trace:
        trace.write(f'{cat} {s}' + '\n')

def _emu_trace(*args):
    _write_trace('EMU', ' | '.join(map(str, args)))

def _get_next_id():
    global _next_id
    _next_id += 1
    return _next_id


#--------- Public hooks for emulation ------------

def set_settings(settings):
    # Explicitly set settings because mocking is a bit convoluted.
    global _settings
    _settings = Settings()
    _settings._settings_storage = settings


def ext_trace(s):
    _write_trace('EXT', s)

_write_trace('===', f'{str(datetime.datetime.now())}'[0:-3])

#------------------------------------------------------------
#---------------- sublime_plugin emmulation -----------------
#------------------------------------------------------------

class CommandInputHandler():
    pass


class TextInputHandler(CommandInputHandler):
    pass


class ListInputHandler(CommandInputHandler):
    pass


class Command():
    pass


class WindowCommand(Command):
    def __init__(self, window):
        self._window = window


class TextCommand(Command):
    def __init__(self, view):
        self._view = view


class EventListener():
    pass


class ViewEventListener():
    def __init__(self, view):
        self._view = view


class ZipImporter:
    pass


#------------------------------------------------------------
#---------------- sublime.definitions -----------------------
#------------------------------------------------------------

TRANSIENT = 4
IGNORECASE = 2
LITERAL = 1


#------------------------------------------------------------
#---------------- sublime.functions() -----------------------
#------------------------------------------------------------

def arch():
    return 'x64'

def platform():
    if sys.platform == 'darwin':
        return 'osx'
    if sys.platform == 'win32':
        return 'windows'
    return 'linux'

def version():
    return '4143'

def packages_path():
    return os.path.expandvars('$APPDATA\\Sublime Text\\Packages')

def executable_path():
    raise NotImplementedError()

def installed_packages_path():
    raise NotImplementedError()

def status_message(msg):
    _emu_trace(f'status_message():{msg}')

def error_message(msg):
    _emu_trace(f'error_message():{msg}')

def message_dialog(msg):
    _emu_trace(f'message_dialog():{msg}')

def ok_cancel_dialog(msg, ok_title=""):
    _emu_trace(f'ok_cancel_dialog():{msg}')
    return True

def run_command(cmd, args=None):
    # Run the named ApplicationCommand.
    _emu_trace(f'run_command():{cmd} {args}')

def set_clipboard(text):
    global _clipboard
    _clipboard = text

def get_clipboard():
    global _clipboard
    return _clipboard

def load_settings(base_name):
    # global _settings
    # if _settings is None:  # lazy init
    # with open(base_name) as fp:
    #     _settings = Settings()
    #     _settings.settings_storage = json.load(fp)
    return _settings

def set_timeout(f, timeout_ms=0):
    # Schedules a function to be called in the future. Sublime Text will block while the function is running.
    time.sleep(float(timeout_ms) / 1000.0)
    f()

def active_window():
    global _active_window
    return _active_window


#------------------------------------------------------------
#---------------- sublime.View ------------------------------
#------------------------------------------------------------

class View():

    def __init__(self, view_id):
        self._view_id = view_id
        self._window = Window(-1)
        self._name = None
        self._file_name = None
        self._buffer = ''
        self._selection = Selection(view_id)
        self._scratch = False
        self._regions = []
        self._syntax = None

    def __len__(self):
        return len(self._buffer)

    def __eq__(self, other):
        return isinstance(other, View) and other.view_id == self._view_id

    def __bool__(self):
        return self._view_id != 0

    def __repr__(self):
        return f'View view_id:{self._view_id} file_name:{self._file_name}'

    def id(self):
        return self._view_id

    def window(self):
        return self._window

    def file_name(self):
        return self._file_name

    def is_loading(self):
        return False

    def close(self):
        _emu_trace('View.close()')
        return True

    def is_scratch(self):
        return self._scratch

    def set_scratch(self, scratch):
        self._scratch = scratch

    def size(self):
        return len(self._buffer)

    def syntax(self):
        return self._syntax

    def settings(self):
        global _settings
        return _settings

    def set_name(self, name):
        self._name = name

    def show_popup(self, content, flags=0, location=-1, max_width=320, max_height=240, on_navigate=None, on_hide=None):
        _emu_trace(f'View.show_popup():{content}')
        raise NotImplementedError()

    def run_command(self, cmd, args=None):
        # Run the named TextCommand
        _emu_trace(f'View.run_command():{cmd} {args}')

    def sel(self):
        return self._selection
        # raise NotImplementedError()

    def set_status(self, key, value):
        _emu_trace(f'set_status(): key:{key} value:{value}')

    #--------- Translation between row/col and index ------------

    def rowcol(self, point):
        # Get row and column for the point.
        point = self._validate(point).a
        row = 0
        col = 0
        for index in range(point):
            if self._buffer[index] == '\n':
                row += 1
                col = 0
            else:
                col += 1
        return (row, col)

    def text_point(self, row, col):
        # Calculates the character offset of the given, 0-based, row and col
        point = 0
        row_i = 0
        col_i = 0
        found = False

        for index in range(len(self._buffer)):
            if row_i == row and col_i == col:
                found = True
                break
            else: # bump
                if self._buffer[index] == '\n':
                    point += 1
                    row_i += 1
                    col_i = 0
                else:
                    point += 1
                    col_i += 1

        return point

    #------------ Find ops ---------------------------

    def find(self, pattern, start_pt, flags=0):
        start_pt = self._validate(start_pt).a
        if flags != 0:
            raise NotImplementedError('args')

        pos = self._buffer.find(pattern, start_pt)
        return Region(pos, pos + len(pattern)) if pos >= 0 else None

    def find_all(self, pattern, flags=0, fmt=None, extractions=None):
        regions = []
        ind = 0

        if flags != 0 or fmt is not None or extractions is not None:
            raise NotImplementedError('args')

        done = False
        while not done:
            region = self.find(pattern, ind, flags)
            if region is not None:
                regions.append(region)
                ind = region.b + 1
            else:
                done = True

        return regions

    def substr(self, x):
        # The char at the Point or within the Region provided.
        region = self._validate(x)
        return self._buffer[region.a:region.b]

    def word(self, x):
        # The word Region that contains the Point. If a Region is provided its beginning/end are expanded to word boundaries.
        region = self._validate(x)
        return self._find(region.a, region.b, 'word')

    def line(self, x):
        # Returns The line Region that contains the Point or an expanded Region to the beginning/end of lines, excluding the newline character.
        region = self._validate(x)
        return self._find(region.a, region.b, 'line')

    def full_line(self, x):
        # full_line(x: Region | Point) ret: Region The line that contains the Point or an expanded Region to the beginning/end of lines, including the newline character.
        region = self._validate(x)
        return self._find(region.a, region.b, 'full_line')

    #------------------- Edit ops --------------------

    def insert(self, edit, point, text):
        point = self._validate(point, allow_empty=True).a # allow insert in empty
        self._buffer = self._buffer[:point] + text + self._buffer[point:]
        return len(text)

    def replace(self, edit, region, text):
        region = self._validate(region)
        self._buffer = self._buffer[:region.a] + text + self._buffer[region.b:]
        return len(text)

    #------------------- Utilities -------------------

    def split_by_newlines(self, region):
        region = self._validate(region)
        b = self._buffer[region.a:region.b]
        return b.splitlines()

    #------------- Scopes and regions ----------------

    def scope_name(self, point):
        raise NotImplementedError()

    def style_for_scope(self, scope):
        raise NotImplementedError()

    def add_regions(self, key, regions, scope="", icon="", flags=0):
        # self._regions.extend(regions) # key
        raise NotImplementedError()

    def get_regions(self, key):
        raise NotImplementedError()

    def erase_regions(self, key):
        raise NotImplementedError()

    #--------- Public hooks for emulation ------------

    def set_window(self, window):
        self._window = window

    def set_syntax(self, syntax):
        self._syntax = syntax

    def set_selection(self, selection):
        self._selection = selection

    #------------------ Private helpers --------------

    def _validate(self, x, allow_empty=False):
        '''
        Checks arg for validity otherwise throws.
        Returns a valid ordered Region within 0 to max_val inclusive.
        '''
        if self._buffer is None:
            raise ValueError('_buffer is None')
        if not allow_empty and len(self._buffer) == 0:
            raise ValueError('_buffer is empty')

        max_val = max(0, len(self._buffer) - 1)
        if isinstance(x, Region):
            if x.a > max_val or x.b > max_val or x.a < 0 or x.b < 0:
                raise ValueError('region out of range')
        else:  # Point
            if x > max_val or x < 0:
                raise ValueError('point out of range')

        # Gen output.
        a = max(0, x.a) if isinstance(x, Region) else max(0, x)
        b = min(x.b, max_val) if isinstance(x, Region) else min(x, max_val)
        if a > b:
            a, b = b, a
        return Region(a, b)

    def _find(self, start_pt, end_pt, mode):
        # Maybe fix order.
        region = self._validate(Region(start_pt, end_pt))

        # Find space/nl/start before
        ind = start_pt
        done = False
        while not done:
            if ind == 0:
                region.a = ind
                done = True
            elif self._buffer[ind - 1] == '\n':
                region.a = ind
                done = True
            elif mode == 'word' and self._buffer[ind - 1] in string.whitespace:
                region.a = ind
                done = True
            else:
                ind -= 1

        # Find space/nl/end after
        ind = end_pt
        buff_len = len(self._buffer)
        done = False
        while not done:
            if ind >= buff_len:
                region.b = ind - 1
                done = True
            elif self._buffer[ind] == '\n':
                region.b = ind + 1 if mode == 'full_line' else ind
                done = True
            elif mode == 'word' and self._buffer[ind] in string.whitespace:
                region.b = ind
                done = True
            else:
                ind += 1

        return region


#------------------------------------------------------------
#---------------- sublime.Window ----------------------------
#------------------------------------------------------------

class Window():

    def __init__(self, id):
        self._id = id
        self._views = []
        self._active_view = -1  # index into _views
        self._project_data = None

    def __repr__(self):
        return f'Window id:{self._id}'

    def id(self):
        return self._id

    def is_valid(self):
        return self._id is not None

    def active_view(self):
        if self._active_view >= 0:
            return self._views[self._active_view]
        else:
            return None

    def show_input_panel(self, caption, initial_text, on_done, on_change, on_cancel):
        _emu_trace(f'Window.show_input_panel(): {caption}')
        raise NotImplementedError()

    def show_quick_panel(self, items, on_select, flags=0, selected_index=-1, on_highlight=None):
        _emu_trace(f'Window.show_quick_panel(): {items}')
        raise NotImplementedError()

    def create_output_panel(self, name, unlisted=False):
        _emu_trace(f'Window.create_output_panel(): {name}')
        view = View(_get_next_id())
        view.set_name(name)
        return view

    def project_file_name(self):
        return 'StPluginTester.sublime-project'

    def settings(self):
        global _settings
        return _settings

    def run_command(self, cmd, args=None):
        # Run the named WindowCommand.
        _emu_trace(f'Window.run_command():{cmd} {args}')

    def new_file(self, flags=0, syntax=""):
        if flags != 0 or syntax != '':
            raise NotImplementedError('args')

        view = View(_get_next_id)
        view._file_name = ''
        view._window = self
        self._views.append(view)
        return view

    def open_file(self, fname, flags=0, group=-1):
        if flags != 0 or group != -1:
            raise NotImplementedError('args')

        with open(fname, 'r') as file:
            view = View(_get_next_id)
            view._file_name = fname  # hack
            view._window = self
            view.insert(None, 0, file.read())
            self._views.append(view)
            return view

    def find_open_file(self, fname):
        for v in self._views:
            if v._file_name() == fname:
                return v
        return None

    def focus_view(self, view):
        for i in range(len(self._views)):
            if self._views[i].id() == view.id():
                self._active_view = i
                # Maybe execute on_activated()?
                break

    def get_view_index(self, view):
        for i in range(len(self._views)):
            if self._views[i].id() == view.id():
                return i

    def views(self):
        return self._views

    def layout(self):
        raise NotImplementedError()

    def set_project_data(self, v):
        self._project_data = v

    def project_data(self):
        return self._project_data


#------------------------------------------------------------
#---------------- sublime.Edit ------------------------------
#------------------------------------------------------------

class Edit:
    def __init__(self, token):
        self._edit_token = token

    def __repr__(self):
        return f'Edit token:{self._edit_token}'


#------------------------------------------------------------
#---------------- sublime.Region ----------------------------
#------------------------------------------------------------

class Region():
    def __init__(self, a, b=None, xpos=-1):
        if b is None:
            b = a
        self.a = a
        self.b = b
        self.xpos = xpos

    def __repr__(self):
        return f'Region a:{self.a} b:{self.b}'

    def __len__(self):
        return self.size()

    def __eq__(self, rhs):
        return isinstance(rhs, Region) and self.a == rhs.a and self.b == rhs.b

    def __lt__(self, rhs):
        lhs_begin = self.begin()
        rhs_begin = rhs.begin()

        if lhs_begin == rhs_begin:
            return self.end() < rhs.end()
        else:
            return lhs_begin < rhs_begin

    def empty(self):
        return self.a == self.b

    def begin(self):
        if self.a < self.b:
            return self.a
        else:
            return self.b

    def end(self):
        if self.a < self.b:
            return self.b
        else:
            return self.a

    def size(self):
        return abs(self.a - self.b)

    def contains(self, x):
        if isinstance(x, Region):
            return self.contains(x.a) and self.contains(x.b)
        else:
            return x >= self.begin() and x <= self.end()

    def cover(self, rhs):
        a = min(self.begin(), rhs.begin())
        b = max(self.end(), rhs.end())
        if self.a < self.b:
            return Region(a, b)
        else:
            return Region(b, a)

    def intersection(self, rhs):
        if self.end() <= rhs.begin():
            return Region(0)
        if self.begin() >= rhs.end():
            return Region(0)
        return Region(max(self.begin(), rhs.begin()), min(self.end(), rhs.end()))

    def intersects(self, rhs):
        lb = self.begin()
        le = self.end()
        rb = rhs.begin()
        re = rhs.end()
        return (
            (lb == rb and le == re) or
            (rb > lb and rb < le) or (re > lb and re < le) or
            (lb > rb and lb < re) or (le > rb and le < re))


#------------------------------------------------------------
#---------------- sublime.Selection -------------------------
#------------------------------------------------------------

class Selection():

    def __init__(self, view_id):
        self._view_id = view_id
        self._regions = []

    def __iter__(self):  # -> Iterator[Region]:
        i = 0
        n = len(self)
        while i < n:
            yield self._regions[i]
            # yield sublime_api.view_selection_get(self.view_id, i)
            i += 1

    def __len__(self):
        return len(self._regions)

    def __getitem__(self, index):
        if index >= 0 and index < len(self._regions):
            return self._regions[index]
        else:
            raise IndexError()

    def __delitem__(self, index):
        if index >= 0 and index < len(self._regions):
            self._regions.remove(index)
        else:
            raise IndexError()

    def __eq__(self, rhs):
        return rhs is not None and list(self) == list(rhs)

    def __lt__(self, rhs):
        return rhs is not None and list(self) < list(rhs)

    def __bool__(self):
        return self._view_id != 0

    def __repr__(self):
        return f'Selection view_id:{self._view_id} regions:{self._regions})'

    def is_valid(self):
        return self._view_id != 0

    def clear(self):
        self._regions.clear()

    def add(self, x):
        if isinstance(x, Region):
            self._regions.append(Region(x.a, x.b, x.xpos))
        else:
            self._regions.append(Region(x, x, x))

    def contains(self, region):
        for r in self._regions:
            if r.contains(region):
                return True
        return False

    def add_all(self, regions):
        for r in regions:
            self.add(r)

    def subtract(self, region):
        raise NotImplementedError()


#------------------------------------------------------------
#---------------- sublime.Settings --------------------------
#------------------------------------------------------------

class Settings():

    def __init__(self):
        self._settings_storage = {}

    def __len__(self):
        return len(self._settings_storage)

    def __repr__(self):
        return f'Settings:{self._settings_storage}'

    def get(self, key, default=None):
        return self._settings_storage.get(key, default)

    def has(self, key):
        return key in self._settings_storage

    def set(self, key, value):
        self._settings_storage[key] = value


#------------------------------------------------------------
#---------------- sublime.Syntax ----------------------------
#------------------------------------------------------------

class Syntax():

    def __init__(self, path, name, hidden, scope):
        self._path = path
        self._name = name
        self._hidden = hidden
        self._scope = scope

    def name(self):
        return self._name
