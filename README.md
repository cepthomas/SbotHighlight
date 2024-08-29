# Highlight Token

Text colorizing per view with persistence per document.
Loosely based on [StyleToken](https://packagecontrol.io/packages/StyleToken).

Built for ST4 on Windows and Linux.

Select some text and right click to select one of six highlight colors. Other options clear the highlights.
To refresh highlighting while editing, save the file.

After editing color-scheme, you need to close and reopen affected views. Yes, I could fix that.

Some ST limitations:
- The way ST works, you have to define which scope to use for each of the different highlights.
- Coloring for markup.user_hls only supports fore and back colors, unfortunately not font_style.
- Regions added by self.view.add_regions() cannot set the foreground color. The scope color is used
  for the region background color. Also they are not available via extract_scope().

[SublimeBagOfTricks](https://github.com/cepthomas/SublimeBagOfTricks) has a command which may be useful
when picking the scopes for the colors you want.

Persistence files are in `.../Packages/User/.SbotStore` as `*.hls`.


## Commands
| Command                    | Type     | Description                   | Args                                  |
| :--------                  | :------- | :-------                      | :--------                             |
| sbot_highlight_text        | Context  | Highlight text                | hl_index: scope markup.user_hl1 - 6   |
| sbot_clear_highlight       | Context  | Remove specific highlight     | hl_index: scope markup.user_hl1 - 6   |
| sbot_clear_all_highlights  | Context  | Remove all highlights         |                                       |


There is no default `Context.sublime-menu` file in this plugin.
Add the commands you like to your own `User\Context.sublime-menu` file. Typical entries are:
``` json
{ "caption": "HL 1", "command": "sbot_highlight_text", "args" : {"hl_index" : "0"} },
{ "caption": "HL 2", "command": "sbot_highlight_text", "args" : {"hl_index" : "1"} },
{ "caption": "Highlight",
    "children":
    [
        { "caption": "HL 3", "command": "sbot_highlight_text", "args" : {"hl_index" : "2"} },
        { "caption": "HL 4", "command": "sbot_highlight_text", "args" : {"hl_index" : "3"} },
        { "caption": "HL 5", "command": "sbot_highlight_text", "args" : {"hl_index" : "4"} },
        { "caption": "HL 6", "command": "sbot_highlight_text", "args" : {"hl_index" : "5"} },
        { "caption": "-" },
        { "caption": "Clear All Highlights in Project", "command": "sbot_clear_all_highlights" },
    ]
},
{ "caption": "Clear Highlights in File", "command": "sbot_clear_highlights" },
```

## Settings
None

## Colors
New scopes have been added to support this application. Adjust these to taste and add
to your `Packages\User\your.sublime-color-scheme` file. Note that these are also used by other
members of the sbot family.

```json
{ "scope": "markup.user_hl1", "background": "red", "foreground": "white" },
{ "scope": "markup.user_hl2", "background": "green", "foreground": "white" },
{ "scope": "markup.user_hl3", "background": "blue", "foreground": "white" },
{ "scope": "markup.user_hl4", "background": "yellow", "foreground": "black" },
{ "scope": "markup.user_hl5", "background": "lime", "foreground": "black" },
{ "scope": "markup.user_hl6", "background": "cyan", "foreground": "black" },
```
