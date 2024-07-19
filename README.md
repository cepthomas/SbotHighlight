# What It Is

Text colorizing per view with persistence per document.

Built for ST4 on Windows and Linux.

- The way ST works, you have to define which scope to use for each of the different highlights.
- Coloring for markup.user_hls only supports fore and back colors, unfortunately not font_style.
- Regions added by self.view.add_regions() cannot set the foreground color. The scope color is used
    for the region background color. Also they are not available via extract_scope().
- After editing color-scheme, close and reopen affected views.

- [SbotScope](https://github.com/cepthomas/SbotScope) may be useful when picking the scopes for the colors you want.
- Loosely based on [StyleToken](https://packagecontrol.io/packages/StyleToken).
- Persistence file is in `%data_dir%\Packages\User\.SbotStore`.
- To refresh highlighting while editing, save the file.


## Commands
| Command                    | Type     | Description                   | Args                                  |
| :--------                  | :------- | :-------                      | :--------                             |
| sbot_highlight_text        | Context  | Highlight text                | hl_index: scope markup.user_hl1 - 6   |
| sbot_clear_highlight       | Context  | Remove specific highlight     | hl_index: scope markup.user_hl1 - 6   |
| sbot_clear_all_highlights  | Context  | Remove all highlights         |                                       |

## Settings
None

## Colors

New scopes have been added to support this application. Adjust these to taste and add
to your `Packages\User\your.sublime-color-scheme` file. Note that these are shared with other
members of the sbot family.

```
{ "scope": "markup.user_hl1", "background": "red", "foreground": "white" },
{ "scope": "markup.user_hl2", "background": "green", "foreground": "white" },
{ "scope": "markup.user_hl3", "background": "blue", "foreground": "white" },
{ "scope": "markup.user_hl4", "background": "yellow", "foreground": "black" },
{ "scope": "markup.user_hl5", "background": "lime", "foreground": "black" },
{ "scope": "markup.user_hl6", "background": "cyan", "foreground": "black" },
```
