# What It Is

Text colorizing per view with persistence per document.

Built for ST4 on Windows and Linux.

- The way ST works, you have to define which scope to use for each of the different highlights.
- Note that Regions added by self.view.add_regions() can not set the foreground color. The scope color is used
    for the region background color. Also they are not available via extract_scope().

- [SbotScope](https://github.com/cepthomas/SbotScope) may be useful when picking the scopes for the colors you want.
- Loosely based on [StyleToken](https://packagecontrol.io/packages/StyleToken).
- Persistence file is in `%data_dir%\Packages\User\.SbotStore`.


## Commands
| Command                    | Implementation | Description                   | Args                           |
| :--------                  | :-------       | :-------                      | :--------                      |
| sbot_highlight_text        | Context        | Highlight text                | hl_index = scope 1 - 6         |
| sbot_clear_highlight       | Context        | Remove specific highlight     | hl_index = scope 1 - 6         |
| sbot_clear_all_highlights  | Context        | Remove all highlights         |                                |

## Settings
None

## Colors
You need to supply something like these in your sublime-color-scheme file:
```
{ "scope": "markup.user_hl1", "background": "red", "foreground": "white" },
{ "scope": "markup.user_hl2", "background": "green", "foreground": "white" },
{ "scope": "markup.user_hl3", "background": "blue", "foreground": "white" },
{ "scope": "markup.user_hl4", "background": "yellow", "foreground": "black" },
{ "scope": "markup.user_hl5", "background": "lime", "foreground": "black" },
{ "scope": "markup.user_hl6", "background": "cyan", "foreground": "black" },
```
These work for all members of the sbot family.