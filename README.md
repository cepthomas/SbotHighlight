# What It Is
Text colorizing in view with persistence per document.
The way ST works, you have to define which scope to use for each of the different highlights.
[SbotScope](https://github.com/cepthomas/SbotScope) will be useful when picking the scopes for the colors you want.

Loosely based on [StyleToken](https://packagecontrol.io/packages/StyleToken).

Built for ST4 on Windows and Linux.

Requires SbotCommon plugin.

## Commands
| Command                    | Implementation | Description                   | Args         |
| :--------                  | :-------       | :-------                      | :--------    |
| `sbot_highlight_text`      | Context        | Highlight text                | `hl_index` = index 1 through 6 |
| `sbot_clear_highlight`     | Context        | Remove specific highlight     | `hl_index` = index 1 through 6 |
| `sbot_clear_all_highlights`| Context        | Remove all highlights         |  |

## Settings
| Setting              | Description                              | Options   |
| :--------            | :-------                                 | :------   |
| `highlight_scopes`   | List of up to 6 scope names for commands | |

