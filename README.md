# What It Is
Text colorizing in view with auto-persistence by document.
[SbotScope](https://github.com/cepthomas/SbotScope) will be useful when picking the scopes for the colors you want.
Loosely based on [StyleToken](https://packagecontrol.io/packages/StyleToken).

Built for Windows and ST4. Other OSes and ST versions will require some hacking.

## Commands
| Command                  | Implementation | Description |
|:--------                 |:-------        |:-------     |
| sbot_highlight_text      | Context        | Highlight text 1 through 6 from your `highlight_scopes` |
| sbot_clear_highlight     | Context        | Remove highlight in selection |
| sbot_clear_all_highlights| Context        | Remove all highlights |

## Settings
| Setting                  | Description |
|:--------                 |:-------     |
| scopes_to_show           | List of scope names for `sbot_show_scopes` command |

