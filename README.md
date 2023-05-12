# What It Is

Text colorizing per view with persistence per document.

Built for ST4 on Windows and Linux.

- The way ST works, you have to define which scope to use for each of the different highlights.
- Edit the setting `highlight_scopes` to taste. The defaults are just a wild guess.
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
| Setting              | Description                              | Options                                    |
| :--------            | :-------                                 | :------                                    |
| highlight_scopes     | List of up to 6 scope names for commands |                                            |
