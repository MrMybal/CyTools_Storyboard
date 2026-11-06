# Documentation integration notes for coding assistants

This file is for assistants working on the application's documentation. The human manual opens through Documentation.html. Do not import this file into its content, navigation or search index.

```json
{
  "application": "CyTools_Storyboard",
  "version": "0.2.3",
  "entry": "Documentation.html",
  "manifest": "DocData/manifest.json",
  "defaultLocale": "en",
  "publishedLocales": [
    "en",
    "fr"
  ],
  "modules": [
    "gallery",
    "image"
  ]
}
```

## Human reader first

Write the manual for people using the application: clear tasks, useful examples, readable media captions and accessible controls. Preserve the application's own terminology and logo. Show complete labels in tooltips when space requires truncation.

Keep documentation build instructions, AI instructions, migration inventories, audit results and verification history outside the human manual. Store assistant guidance in this DocAI.md sidecar, and keep private working records in the source repository. Mark existing internal Markdown with audience: internal or audience: ai to exclude it from an export.

## Languages

English is the source/default language; a complete French translation is mandatory. Keep the same page IDs and explicit anchors across translations. Translate prose, titles, descriptions, captions, annotations and media explanations; code and API identifiers retain their proper spelling. Do not copy original-language prose into another locale, use placeholders, or declare a partially translated manual complete.

The build fails before publishing when English or French has missing/empty pages or explicitly outdated sourceRevision values. Additional incomplete locales are withheld. This structural check cannot judge translation quality: read the translations before publishing. Do not restore a mixed-language fallback banner or expose incomplete languages in the selector.

## Files and integration

Ship Documentation.html, this DocAI.md, and the complete DocData directory together. The HTML is the reader itself; all runtime scripts, media, styles, notices, manifests and optional version exports are inside DocData. Open the HTML through file:// with no web server, runtime CDN or remote font.

Source Markdown, asset inputs, tooling and the build configuration belong in App/.CyDocBuild/. The CLI looks for .CyDocBuild/cydoc.config.json by default; its output is the sibling App/Documentation/. Edit those inputs and rebuild. Do not edit generated data.js or manifest.json by hand. Authored media and logos use logical assets/ paths; do not prepend DocData in the source content. Custom readers use context.assetUrl for display and retain logical paths for binary providers and annotation identities.

Review documentation against the application's current UI, behavior and public APIs, then correct obsolete descriptions. Organize topics and subpages as a tree. Public function APIs, signatures, includes, imports and modules may be documented; never publish raw source listings or implementation bodies. apiIndex creates API-only references; the legacy sourceIndex option does not restore source browsing. Keep source trees outside the manual's assets.

Select only useful optional modules. A gallery also needs each item's reader; only mesh requires Three.js. Keep image enlargement inside the documentation window and preserve keyboard, touch and Escape controls.

Use Documentation.html#/LOCALE/PAGE/ANCHOR for contextual help, with correctly encoded stable IDs. Preserve existing deep links or add validated aliases. Legacy index.html files may remain solely as compatibility redirects. Test the exported manual and the application's help entry on the target platform; report only checks actually performed.


# CyTools_Storyboard — application integration

Use the installed private Python interpreter and `app/tool.py`. CLI inspection: `describe`, `list-operations`, and `describe-operation OPERATION_ID`; MCP: `mcp`. File inputs accept readable absolute paths and are automatically imported into the task. Export wanted outputs before finishing a temporary task. Never accept a model licence or file modification confirmation for the user.

## Public operation contracts

```json
[
  {
    "id": "create_storyboard",
    "name": "Create a storyboard",
    "description": "Create a project folder (.cystory) with one empty sequence.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "title": {
          "type": "string",
          "minLength": 1,
          "maxLength": 120
        },
        "folder": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Parent folder; default data/projects."
        },
        "aspect": {
          "type": "string",
          "enum": [
            "16:9",
            "21:9",
            "4:3",
            "1:1",
            "3:4",
            "9:16",
            "2.39:1"
          ],
          "default": "16:9"
        },
        "fps": {
          "type": "integer",
          "minimum": 1,
          "maximum": 120,
          "default": 24
        },
        "default_duration": {
          "type": "number",
          "minimum": 0.1,
          "maximum": 600,
          "default": 5
        }
      },
      "required": [
        "title"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "duplicate_storyboard",
    "name": "Save a storyboard as a copy",
    "description": "Copy a project under another title (document and assets, its own folder and id); the original is left as it is.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "title": {
          "type": "string",
          "minLength": 1,
          "maxLength": 120
        },
        "folder": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Parent folder of the copy; default: next to the original."
        }
      },
      "required": [
        "project",
        "title"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "list_storyboards",
    "name": "List storyboards",
    "description": "Projects in data/projects (or in a given folder).",
    "inputSchema": {
      "type": "object",
      "properties": {
        "folder": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096
        }
      },
      "required": [],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "projects": {
          "type": "array"
        }
      },
      "required": [
        "projects"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "describe_storyboard",
    "name": "Describe a storyboard",
    "description": "The whole document, the timeline (start/end of every panel), the total duration and the problems found.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        }
      },
      "required": [
        "project"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "update_storyboard",
    "name": "Change storyboard settings",
    "description": "Title, description and settings.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "title": {
          "type": "string",
          "maxLength": 120
        },
        "description": {
          "type": "string",
          "maxLength": 8000
        },
        "settings": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "aspect": {
              "type": "string",
              "enum": [
                "16:9",
                "21:9",
                "4:3",
                "1:1",
                "3:4",
                "9:16",
                "2.39:1"
              ]
            },
            "fps": {
              "type": "integer",
              "minimum": 1,
              "maximum": 120
            },
            "defaultDuration": {
              "type": "number",
              "minimum": 0.1,
              "maximum": 600
            },
            "minSegment": {
              "type": "number",
              "minimum": 0,
              "maximum": 600
            },
            "maxSegment": {
              "type": "number",
              "minimum": 0.1,
              "maximum": 600
            },
            "style": {
              "type": "string",
              "maxLength": 4000
            },
            "language": {
              "type": "string",
              "maxLength": 40
            }
          }
        }
      },
      "required": [
        "project"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "add_panel",
    "name": "Add a panel",
    "description": "Add a panel at the end of a sequence, or after a given panel.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "sequence": {
          "type": "string"
        },
        "after": {
          "type": "string"
        },
        "title": {
          "type": "string",
          "maxLength": 200
        },
        "duration": {
          "type": "number",
          "minimum": 0.1,
          "maximum": 600,
          "description": "Seconds on screen."
        },
        "status": {
          "type": "string",
          "enum": [
            "idea",
            "draft",
            "ready",
            "generated"
          ]
        },
        "color": {
          "type": "string",
          "maxLength": 20
        },
        "images": {
          "type": "array",
          "maxItems": 30,
          "items": {
            "type": "object",
            "additionalProperties": false,
            "required": [
              "file"
            ],
            "properties": {
              "file": {
                "type": "string",
                "x-cy-kind": "File",
                "maxLength": 4096,
                "description": "Local file; copied into the project assets."
              },
              "role": {
                "type": "string",
                "enum": [
                  "sketch",
                  "first",
                  "last",
                  "keyframe",
                  "reference"
                ],
                "default": "sketch"
              },
              "time": {
                "type": "number",
                "minimum": 0,
                "description": "For keyframes: seconds from the start of the panel."
              },
              "caption": {
                "type": "string",
                "maxLength": 500
              }
            }
          }
        },
        "prompt": {
          "type": "object",
          "additionalProperties": false,
          "x-cy-kind": "Object",
          "properties": {
            "scene": {
              "type": "string",
              "maxLength": 4000,
              "x-cy-kind": "MultilineString"
            },
            "action": {
              "type": "string",
              "maxLength": 8000,
              "x-cy-kind": "MultilineString"
            },
            "shotSize": {
              "type": "string",
              "enum": [
                "",
                "extreme wide shot",
                "wide shot",
                "full shot",
                "medium wide shot",
                "medium shot",
                "medium close-up",
                "close-up",
                "extreme close-up",
                "insert shot",
                "over-the-shoulder shot"
              ]
            },
            "angle": {
              "type": "string",
              "enum": [
                "",
                "eye level",
                "high angle",
                "low angle",
                "bird's-eye view",
                "worm's-eye view",
                "dutch angle",
                "POV"
              ]
            },
            "cameraMove": {
              "type": "string",
              "enum": [
                "",
                "static shot",
                "push in",
                "pull out",
                "zoom in",
                "zoom out",
                "pan left",
                "pan right",
                "truck left",
                "truck right",
                "tilt up",
                "tilt down",
                "pedestal up",
                "pedestal down",
                "arc shot",
                "tracking shot",
                "handheld",
                "shake slightly",
                "shake strongly",
                "roll clockwise",
                "roll counterclockwise"
              ]
            },
            "cameraAmplitude": {
              "type": "string",
              "enum": [
                "",
                "small",
                "large"
              ]
            },
            "cameraSpeed": {
              "type": "string",
              "enum": [
                "",
                "slow",
                "fast"
              ]
            },
            "lens": {
              "type": "string",
              "maxLength": 100
            },
            "sound": {
              "type": "string",
              "maxLength": 2000
            },
            "music": {
              "type": "string",
              "maxLength": 2000
            },
            "dialogue": {
              "type": "array",
              "maxItems": 50,
              "items": {
                "type": "object",
                "additionalProperties": false,
                "properties": {
                  "speaker": {
                    "type": "string",
                    "maxLength": 200,
                    "description": "Library character id or a free name."
                  },
                  "language": {
                    "type": "string",
                    "maxLength": 40,
                    "default": "English"
                  },
                  "line": {
                    "type": "string",
                    "maxLength": 2000
                  },
                  "offScreen": {
                    "type": "boolean",
                    "default": false
                  },
                  "delivery": {
                    "type": "string",
                    "maxLength": 200
                  }
                }
              }
            },
            "freeText": {
              "type": "string",
              "maxLength": 60000,
              "x-cy-kind": "MultilineString",
              "description": "Anything else, written as you want it passed on."
            }
          }
        },
        "references": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Library item ids."
        },
        "transition": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "type": {
              "type": "string",
              "enum": [
                "cut",
                "crossfade",
                "fade to black",
                "fade from black"
              ]
            },
            "duration": {
              "type": "number",
              "minimum": 0,
              "maximum": 10
            }
          }
        },
        "notes": {
          "type": "string",
          "maxLength": 8000,
          "x-cy-kind": "MultilineString"
        }
      },
      "required": [
        "project"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "update_panel",
    "name": "Change a panel",
    "description": "Change any field of a panel; prompt fields are merged.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "panel": {
          "type": "string"
        },
        "title": {
          "type": "string",
          "maxLength": 200
        },
        "duration": {
          "type": "number",
          "minimum": 0.1,
          "maximum": 600,
          "description": "Seconds on screen."
        },
        "status": {
          "type": "string",
          "enum": [
            "idea",
            "draft",
            "ready",
            "generated"
          ]
        },
        "color": {
          "type": "string",
          "maxLength": 20
        },
        "images": {
          "type": "array",
          "maxItems": 30,
          "items": {
            "type": "object",
            "additionalProperties": false,
            "required": [
              "file"
            ],
            "properties": {
              "file": {
                "type": "string",
                "x-cy-kind": "File",
                "maxLength": 4096,
                "description": "Local file; copied into the project assets."
              },
              "role": {
                "type": "string",
                "enum": [
                  "sketch",
                  "first",
                  "last",
                  "keyframe",
                  "reference"
                ],
                "default": "sketch"
              },
              "time": {
                "type": "number",
                "minimum": 0,
                "description": "For keyframes: seconds from the start of the panel."
              },
              "caption": {
                "type": "string",
                "maxLength": 500
              }
            }
          }
        },
        "prompt": {
          "type": "object",
          "additionalProperties": false,
          "x-cy-kind": "Object",
          "properties": {
            "scene": {
              "type": "string",
              "maxLength": 4000,
              "x-cy-kind": "MultilineString"
            },
            "action": {
              "type": "string",
              "maxLength": 8000,
              "x-cy-kind": "MultilineString"
            },
            "shotSize": {
              "type": "string",
              "enum": [
                "",
                "extreme wide shot",
                "wide shot",
                "full shot",
                "medium wide shot",
                "medium shot",
                "medium close-up",
                "close-up",
                "extreme close-up",
                "insert shot",
                "over-the-shoulder shot"
              ]
            },
            "angle": {
              "type": "string",
              "enum": [
                "",
                "eye level",
                "high angle",
                "low angle",
                "bird's-eye view",
                "worm's-eye view",
                "dutch angle",
                "POV"
              ]
            },
            "cameraMove": {
              "type": "string",
              "enum": [
                "",
                "static shot",
                "push in",
                "pull out",
                "zoom in",
                "zoom out",
                "pan left",
                "pan right",
                "truck left",
                "truck right",
                "tilt up",
                "tilt down",
                "pedestal up",
                "pedestal down",
                "arc shot",
                "tracking shot",
                "handheld",
                "shake slightly",
                "shake strongly",
                "roll clockwise",
                "roll counterclockwise"
              ]
            },
            "cameraAmplitude": {
              "type": "string",
              "enum": [
                "",
                "small",
                "large"
              ]
            },
            "cameraSpeed": {
              "type": "string",
              "enum": [
                "",
                "slow",
                "fast"
              ]
            },
            "lens": {
              "type": "string",
              "maxLength": 100
            },
            "sound": {
              "type": "string",
              "maxLength": 2000
            },
            "music": {
              "type": "string",
              "maxLength": 2000
            },
            "dialogue": {
              "type": "array",
              "maxItems": 50,
              "items": {
                "type": "object",
                "additionalProperties": false,
                "properties": {
                  "speaker": {
                    "type": "string",
                    "maxLength": 200,
                    "description": "Library character id or a free name."
                  },
                  "language": {
                    "type": "string",
                    "maxLength": 40,
                    "default": "English"
                  },
                  "line": {
                    "type": "string",
                    "maxLength": 2000
                  },
                  "offScreen": {
                    "type": "boolean",
                    "default": false
                  },
                  "delivery": {
                    "type": "string",
                    "maxLength": 200
                  }
                }
              }
            },
            "freeText": {
              "type": "string",
              "maxLength": 60000,
              "x-cy-kind": "MultilineString",
              "description": "Anything else, written as you want it passed on."
            }
          }
        },
        "references": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Library item ids."
        },
        "transition": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "type": {
              "type": "string",
              "enum": [
                "cut",
                "crossfade",
                "fade to black",
                "fade from black"
              ]
            },
            "duration": {
              "type": "number",
              "minimum": 0,
              "maximum": 10
            }
          }
        },
        "notes": {
          "type": "string",
          "maxLength": 8000,
          "x-cy-kind": "MultilineString"
        }
      },
      "required": [
        "project",
        "panel"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "duplicate_panel",
    "name": "Duplicate a panel",
    "description": "Copy a panel right after itself.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "panel": {
          "type": "string"
        }
      },
      "required": [
        "project",
        "panel"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "move_panel",
    "name": "Move a panel",
    "description": "Move a panel to a position, in its sequence or another one.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "panel": {
          "type": "string"
        },
        "sequence": {
          "type": "string"
        },
        "index": {
          "type": "integer",
          "minimum": 0
        }
      },
      "required": [
        "project",
        "panel"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "remove_panel",
    "name": "Remove a panel",
    "description": "Delete a panel (its assets stay in the project).",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "panel": {
          "type": "string"
        }
      },
      "required": [
        "project",
        "panel"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "add_sequence",
    "name": "Add a sequence",
    "description": "A new group of panels.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "title": {
          "type": "string",
          "maxLength": 200
        },
        "after": {
          "type": "string"
        }
      },
      "required": [
        "project"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "update_sequence",
    "name": "Change a sequence",
    "description": "Title, colour, notes.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "sequence": {
          "type": "string"
        },
        "title": {
          "type": "string",
          "maxLength": 200
        },
        "color": {
          "type": "string",
          "maxLength": 20
        },
        "notes": {
          "type": "string",
          "maxLength": 8000
        }
      },
      "required": [
        "project",
        "sequence"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "remove_sequence",
    "name": "Remove a sequence",
    "description": "Delete a sequence and its panels.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "sequence": {
          "type": "string"
        }
      },
      "required": [
        "project",
        "sequence"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "add_library_item",
    "name": "Add a reference",
    "description": "A character, location, object, style, image, audio or video reference usable by any panel.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "kind": {
          "type": "string",
          "enum": [
            "character",
            "location",
            "object",
            "style",
            "image",
            "audio",
            "video"
          ]
        },
        "name": {
          "type": "string",
          "maxLength": 200
        },
        "description": {
          "type": "string",
          "maxLength": 8000
        },
        "files": {
          "type": "array",
          "maxItems": 20,
          "items": {
            "type": "string",
            "x-cy-kind": "File",
            "maxLength": 4096,
            "description": "Local file; copied into the project assets."
          }
        },
        "tags": {
          "type": "array",
          "items": {
            "type": "string",
            "maxLength": 60
          }
        }
      },
      "required": [
        "project",
        "kind",
        "name"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "update_library_item",
    "name": "Change a reference",
    "description": "Name, description, kind, files, tags.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "item": {
          "type": "string"
        },
        "kind": {
          "type": "string",
          "enum": [
            "character",
            "location",
            "object",
            "style",
            "image",
            "audio",
            "video"
          ]
        },
        "name": {
          "type": "string",
          "maxLength": 200
        },
        "description": {
          "type": "string",
          "maxLength": 8000
        },
        "files": {
          "type": "array",
          "maxItems": 20,
          "items": {
            "type": "string",
            "x-cy-kind": "File",
            "maxLength": 4096,
            "description": "Local file; copied into the project assets."
          }
        },
        "tags": {
          "type": "array",
          "items": {
            "type": "string",
            "maxLength": 60
          }
        }
      },
      "required": [
        "project",
        "item"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "remove_library_item",
    "name": "Remove a reference",
    "description": "Also removed from the panels that used it.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "item": {
          "type": "string"
        }
      },
      "required": [
        "project",
        "item"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "validate_storyboard",
    "name": "Check a storyboard",
    "description": "Missing images, empty panels, durations outside the limits, unknown references.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        }
      },
      "required": [
        "project"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "export_contact_sheet",
    "name": "Export a contact sheet",
    "description": "All panels on one PNG with numbers, durations and text.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "columns": {
          "type": "integer",
          "minimum": 1,
          "maximum": 10,
          "default": 4
        },
        "cell_width": {
          "type": "integer",
          "minimum": 160,
          "maximum": 1200,
          "default": 480
        }
      },
      "required": [
        "project"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "file": {
          "type": "string",
          "x-cy-kind": "Image"
        }
      },
      "required": [
        "file"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "export_summary",
    "name": "Export a script",
    "description": "The storyboard as Markdown or as one self-contained HTML page.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "format": {
          "type": "string",
          "enum": [
            "md",
            "html"
          ],
          "default": "html"
        }
      },
      "required": [
        "project"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "file": {
          "type": "string"
        }
      },
      "required": [
        "file"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "export_animatic",
    "name": "Export an animatic",
    "description": "Every panel for its duration with its transition, as an MP4 (captions optional); a panel staged in 3D plays its camera, character and pose moves.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "captions": {
          "type": "boolean",
          "default": true
        },
        "fps": {
          "type": "integer",
          "minimum": 1,
          "maximum": 60,
          "default": 24
        },
        "motion": {
          "type": "boolean",
          "default": true,
          "description": "Render the moves of 3D panels (off: one picture per panel)."
        },
        "motion_fps": {
          "type": "integer",
          "minimum": 4,
          "maximum": 24,
          "default": 12,
          "description": "Rendered pictures per second for 3D moves."
        }
      },
      "required": [
        "project"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "file": {
          "type": "string",
          "x-cy-kind": "Video"
        },
        "duration": {
          "type": "number"
        }
      },
      "required": [
        "file"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": true
  },
  {
    "id": "add_stage",
    "name": "Add a 3D stage",
    "description": "A 3D set of simple shapes that panels can be framed in; several panels sharing one stage keep the same places from one shot to the next.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "name": {
          "type": "string",
          "maxLength": 200
        }
      },
      "required": [
        "project"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "update_stage",
    "name": "Change a 3D stage",
    "description": "Name, sky colour, ground on/off and colour.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "stage": {
          "type": "string"
        },
        "name": {
          "type": "string",
          "maxLength": 200
        },
        "sky": {
          "type": "string",
          "maxLength": 20
        },
        "ground": {
          "type": "boolean"
        },
        "groundColour": {
          "type": "string",
          "maxLength": 20
        }
      },
      "required": [
        "project",
        "stage"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "remove_stage",
    "name": "Remove a 3D stage",
    "description": "Panels framed in it go back to their images.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "stage": {
          "type": "string"
        }
      },
      "required": [
        "project",
        "stage"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "add_object",
    "name": "Add a shape to a stage",
    "description": "Box, sphere, cylinder, cone, capsule, plane, mannequin, or an imported mesh (.glb .gltf .obj .ply .stl .off). New shapes stand on the ground.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "stage": {
          "type": "string"
        },
        "shape": {
          "type": "string",
          "enum": [
            "box",
            "sphere",
            "cylinder",
            "cone",
            "capsule",
            "plane",
            "mannequin",
            "mesh"
          ],
          "default": "box"
        },
        "mesh": {
          "type": "string",
          "x-cy-kind": "File",
          "maxLength": 4096,
          "description": "Mesh file, for shape = mesh."
        },
        "name": {
          "type": "string",
          "maxLength": 200
        },
        "color": {
          "type": "string",
          "maxLength": 20
        },
        "position": {
          "type": "array",
          "items": {
            "type": "number"
          },
          "minItems": 3,
          "maxItems": 4
        },
        "rotation": {
          "type": "array",
          "items": {
            "type": "number"
          },
          "minItems": 3,
          "maxItems": 4,
          "description": "Degrees around X, Y, Z."
        },
        "scale": {
          "type": "array",
          "items": {
            "type": "number"
          },
          "minItems": 3,
          "maxItems": 4,
          "description": "Size in metres for box/sphere/cylinder/cone, a factor for the others."
        },
        "role": {
          "type": "string",
          "enum": [
            "set",
            "character",
            "object",
            "location"
          ]
        },
        "reference": {
          "type": "string",
          "description": "Library item this shape stands for."
        },
        "pose": {
          "type": "string",
          "description": "Character pose on the stage: a preset or a project pose id."
        }
      },
      "required": [
        "project",
        "stage"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "update_object",
    "name": "Change a shape",
    "description": "Change a shape on its stage (every panel using the stage sees it).",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "object": {
          "type": "string"
        },
        "name": {
          "type": "string",
          "maxLength": 200
        },
        "color": {
          "type": "string",
          "maxLength": 20
        },
        "position": {
          "type": "array",
          "items": {
            "type": "number"
          },
          "minItems": 3,
          "maxItems": 4
        },
        "rotation": {
          "type": "array",
          "items": {
            "type": "number"
          },
          "minItems": 3,
          "maxItems": 4,
          "description": "Degrees around X, Y, Z."
        },
        "scale": {
          "type": "array",
          "items": {
            "type": "number"
          },
          "minItems": 3,
          "maxItems": 4,
          "description": "Size in metres for box/sphere/cylinder/cone, a factor for the others."
        },
        "role": {
          "type": "string",
          "enum": [
            "set",
            "character",
            "object",
            "location"
          ]
        },
        "reference": {
          "type": "string",
          "description": "Library item this shape stands for."
        },
        "pose": {
          "type": "string",
          "description": "Character pose on the stage: a preset or a project pose id."
        }
      },
      "required": [
        "project",
        "object"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "duplicate_object",
    "name": "Duplicate a shape",
    "description": "A copy one metre to the right.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "object": {
          "type": "string"
        }
      },
      "required": [
        "project",
        "object"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "remove_object",
    "name": "Remove a shape",
    "description": "Also removes its per-panel placements.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "object": {
          "type": "string"
        }
      },
      "required": [
        "project",
        "object"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "add_pose",
    "name": "Add a character pose",
    "description": "A project pose made joint by joint, starting from a preset (standing, walking, running, sitting, crouching, arms raised, pointing) or another project pose; usable as the pose or end pose of any character.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "name": {
          "type": "string",
          "maxLength": 120
        },
        "base": {
          "type": "string",
          "default": "standing"
        },
        "angles": {
          "type": "object",
          "additionalProperties": false,
          "description": "Degrees; values not given are kept.",
          "properties": {
            "lean": {
              "type": "number",
              "minimum": -45,
              "maximum": 90,
              "description": "Upper body forwards."
            },
            "twist": {
              "type": "number",
              "minimum": -90,
              "maximum": 90,
              "description": "Upper body to its left."
            },
            "bend": {
              "type": "number",
              "minimum": -45,
              "maximum": 45,
              "description": "Upper body tilted to its left side."
            },
            "tilt": {
              "type": "number",
              "minimum": -25,
              "maximum": 25,
              "description": "Pelvis tilted, left hip up; the legs hang from it, the upper body stays."
            },
            "head": {
              "type": "array",
              "items": {
                "type": "number"
              },
              "minItems": 2,
              "maxItems": 2,
              "description": "[turn to its left (-80..80), tilt up (-45..60)]"
            },
            "seat": {
              "type": [
                "number",
                "null"
              ],
              "minimum": 0.2,
              "maximum": 1.2,
              "description": "Pelvis height in metres when seated; null = on its feet."
            },
            "r_arm": {
              "type": "array",
              "items": {
                "type": "number"
              },
              "minItems": 3,
              "maxItems": 4,
              "description": "[raise forwards (-60..180), raise sideways (-20..180), elbow bend (0..150), turn of the arm about itself, forearm outwards (-90..90, optional)]"
            },
            "l_arm": {
              "type": "array",
              "items": {
                "type": "number"
              },
              "minItems": 3,
              "maxItems": 4
            },
            "r_leg": {
              "type": "array",
              "items": {
                "type": "number"
              },
              "minItems": 3,
              "maxItems": 4,
              "description": "[raise forwards (-45..130), raise sideways (-30..60), knee bend (0..150), turn of the leg about itself, knee outwards (-45..45, optional)]"
            },
            "l_leg": {
              "type": "array",
              "items": {
                "type": "number"
              },
              "minItems": 3,
              "maxItems": 4
            },
            "r_hand": {
              "type": "array",
              "items": {
                "type": "number"
              },
              "minItems": 6,
              "maxItems": 8,
              "description": "[curl of the thumb, index, middle, ring, little finger (0..100 %), spread of the fingers (0..30 degrees), wrist bent towards the palm (-70..80), towards the thumb (-25..35), both optional]"
            },
            "l_hand": {
              "type": "array",
              "items": {
                "type": "number"
              },
              "minItems": 6,
              "maxItems": 8
            },
            "r_foot": {
              "type": "array",
              "items": {
                "type": "number"
              },
              "minItems": 2,
              "maxItems": 2,
              "description": "[foot pitched toes down: on tiptoe when positive (-30..60), toes bent up (-40..70)]; the foot is flat on the ground at 0."
            },
            "l_foot": {
              "type": "array",
              "items": {
                "type": "number"
              },
              "minItems": 2,
              "maxItems": 2
            }
          }
        },
        "walks": {
          "type": "boolean",
          "default": true,
          "description": "The legs walk when a character in this pose moves."
        }
      },
      "required": [
        "project"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "update_pose",
    "name": "Change a character pose",
    "description": "Rename a project pose or change some of its joints.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "pose": {
          "type": "string"
        },
        "name": {
          "type": "string",
          "maxLength": 120
        },
        "angles": {
          "type": "object",
          "additionalProperties": false,
          "description": "Degrees; values not given are kept.",
          "properties": {
            "lean": {
              "type": "number",
              "minimum": -45,
              "maximum": 90,
              "description": "Upper body forwards."
            },
            "twist": {
              "type": "number",
              "minimum": -90,
              "maximum": 90,
              "description": "Upper body to its left."
            },
            "bend": {
              "type": "number",
              "minimum": -45,
              "maximum": 45,
              "description": "Upper body tilted to its left side."
            },
            "tilt": {
              "type": "number",
              "minimum": -25,
              "maximum": 25,
              "description": "Pelvis tilted, left hip up; the legs hang from it, the upper body stays."
            },
            "head": {
              "type": "array",
              "items": {
                "type": "number"
              },
              "minItems": 2,
              "maxItems": 2,
              "description": "[turn to its left (-80..80), tilt up (-45..60)]"
            },
            "seat": {
              "type": [
                "number",
                "null"
              ],
              "minimum": 0.2,
              "maximum": 1.2,
              "description": "Pelvis height in metres when seated; null = on its feet."
            },
            "r_arm": {
              "type": "array",
              "items": {
                "type": "number"
              },
              "minItems": 3,
              "maxItems": 4,
              "description": "[raise forwards (-60..180), raise sideways (-20..180), elbow bend (0..150), turn of the arm about itself, forearm outwards (-90..90, optional)]"
            },
            "l_arm": {
              "type": "array",
              "items": {
                "type": "number"
              },
              "minItems": 3,
              "maxItems": 4
            },
            "r_leg": {
              "type": "array",
              "items": {
                "type": "number"
              },
              "minItems": 3,
              "maxItems": 4,
              "description": "[raise forwards (-45..130), raise sideways (-30..60), knee bend (0..150), turn of the leg about itself, knee outwards (-45..45, optional)]"
            },
            "l_leg": {
              "type": "array",
              "items": {
                "type": "number"
              },
              "minItems": 3,
              "maxItems": 4
            },
            "r_hand": {
              "type": "array",
              "items": {
                "type": "number"
              },
              "minItems": 6,
              "maxItems": 8,
              "description": "[curl of the thumb, index, middle, ring, little finger (0..100 %), spread of the fingers (0..30 degrees), wrist bent towards the palm (-70..80), towards the thumb (-25..35), both optional]"
            },
            "l_hand": {
              "type": "array",
              "items": {
                "type": "number"
              },
              "minItems": 6,
              "maxItems": 8
            },
            "r_foot": {
              "type": "array",
              "items": {
                "type": "number"
              },
              "minItems": 2,
              "maxItems": 2,
              "description": "[foot pitched toes down: on tiptoe when positive (-30..60), toes bent up (-40..70)]; the foot is flat on the ground at 0."
            },
            "l_foot": {
              "type": "array",
              "items": {
                "type": "number"
              },
              "minItems": 2,
              "maxItems": 2
            }
          }
        },
        "walks": {
          "type": "boolean"
        }
      },
      "required": [
        "project",
        "pose"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "remove_pose",
    "name": "Remove a character pose",
    "description": "The characters using it go back to standing.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "pose": {
          "type": "string"
        }
      },
      "required": [
        "project",
        "pose"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "set_panel_layout",
    "name": "Stage a panel",
    "description": "Choose how a panel is laid out: its images (image), a 2D drawing, or a shot on a 3D stage with a start camera and an optional end camera.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "panel": {
          "type": "string"
        },
        "mode": {
          "type": "string",
          "enum": [
            "image",
            "2d",
            "3d"
          ]
        },
        "stage": {
          "type": "string"
        },
        "camera": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "position",
            "target"
          ],
          "properties": {
            "position": {
              "type": "array",
              "items": {
                "type": "number"
              },
              "minItems": 3,
              "maxItems": 4,
              "description": "Metres; Y is up, the ground is Y = 0."
            },
            "target": {
              "type": "array",
              "items": {
                "type": "number"
              },
              "minItems": 3,
              "maxItems": 4,
              "description": "The point the camera looks at."
            },
            "fov": {
              "type": "number",
              "minimum": 5,
              "maximum": 150,
              "default": 40,
              "description": "Vertical field of view, degrees."
            },
            "roll": {
              "type": "number",
              "minimum": -180,
              "maximum": 180,
              "default": 0
            }
          }
        },
        "cameraEnd": {
          "anyOf": [
            {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "position",
                "target"
              ],
              "properties": {
                "position": {
                  "type": "array",
                  "items": {
                    "type": "number"
                  },
                  "minItems": 3,
                  "maxItems": 4,
                  "description": "Metres; Y is up, the ground is Y = 0."
                },
                "target": {
                  "type": "array",
                  "items": {
                    "type": "number"
                  },
                  "minItems": 3,
                  "maxItems": 4,
                  "description": "The point the camera looks at."
                },
                "fov": {
                  "type": "number",
                  "minimum": 5,
                  "maximum": 150,
                  "default": 40,
                  "description": "Vertical field of view, degrees."
                },
                "roll": {
                  "type": "number",
                  "minimum": -180,
                  "maximum": 180,
                  "default": 0
                }
              }
            },
            {
              "type": "null"
            }
          ]
        },
        "drawing": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "background": {
              "type": "string",
              "maxLength": 20
            },
            "items": {
              "type": "array",
              "maxItems": 500,
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "type",
                  "points"
                ],
                "properties": {
                  "type": {
                    "type": "string",
                    "enum": [
                      "rect",
                      "ellipse",
                      "line",
                      "arrow",
                      "stroke",
                      "text",
                      "figure"
                    ]
                  },
                  "points": {
                    "type": "array",
                    "maxItems": 2000,
                    "items": {
                      "type": "array",
                      "items": {
                        "type": "number"
                      },
                      "minItems": 2,
                      "maxItems": 2
                    },
                    "description": "Coordinates from 0 to 1 of the frame (x right, y down). Two corners for rect/ellipse, start and end for line/arrow, the path for stroke, one point for text and figure (a figure stands on it)."
                  },
                  "color": {
                    "type": "string",
                    "maxLength": 20
                  },
                  "width": {
                    "type": "number",
                    "minimum": 0.5,
                    "maximum": 50
                  },
                  "fill": {
                    "type": "boolean"
                  },
                  "text": {
                    "type": "string",
                    "maxLength": 500
                  },
                  "size": {
                    "type": "number",
                    "minimum": 0.005,
                    "maximum": 1,
                    "description": "Text height or figure scale (share of the frame)."
                  }
                }
              }
            }
          }
        }
      },
      "required": [
        "project",
        "panel"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "override_object",
    "name": "Place a shape in one panel",
    "description": "Move, turn, resize or hide a shape in this panel only (a character walking between shots); clear = back to the stage placement.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "panel": {
          "type": "string"
        },
        "object": {
          "type": "string"
        },
        "position": {
          "type": "array",
          "items": {
            "type": "number"
          },
          "minItems": 3,
          "maxItems": 4
        },
        "rotation": {
          "type": "array",
          "items": {
            "type": "number"
          },
          "minItems": 3,
          "maxItems": 4
        },
        "scale": {
          "type": "array",
          "items": {
            "type": "number"
          },
          "minItems": 3,
          "maxItems": 4
        },
        "hidden": {
          "type": "boolean"
        },
        "positionEnd": {
          "anyOf": [
            {
              "type": "array",
              "items": {
                "type": "number"
              },
              "minItems": 3,
              "maxItems": 4
            },
            {
              "type": "null"
            }
          ],
          "description": "Where it is at the end of the panel (it moves there); null = still."
        },
        "rotationEnd": {
          "anyOf": [
            {
              "type": "array",
              "items": {
                "type": "number"
              },
              "minItems": 3,
              "maxItems": 4
            },
            {
              "type": "null"
            }
          ]
        },
        "pose": {
          "type": "string",
          "description": "Character pose in this panel: standing, walking, running, sitting, crouching, arms raised, pointing or a project pose id (add_pose)."
        },
        "poseEnd": {
          "type": "string",
          "description": "Pose at the end of the panel (same values)."
        },
        "clear": {
          "type": "boolean",
          "default": false
        }
      },
      "required": [
        "project",
        "panel",
        "object"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string"
        },
        "document": {
          "type": "object"
        },
        "timeline": {
          "type": "array"
        },
        "totalDuration": {
          "type": "number"
        },
        "issues": {
          "type": "array"
        }
      },
      "required": [
        "project"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "render_panel_layout",
    "name": "Render a panel layout",
    "description": "Render the 2D drawing or the 3D shot (from the start or end camera) into the project; it becomes the panel picture. 3D also writes a depth map.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "panel": {
          "type": "string"
        },
        "camera": {
          "type": "string",
          "enum": [
            "start",
            "end"
          ],
          "default": "start"
        }
      },
      "required": [
        "project",
        "panel"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "render": {
          "type": "string",
          "x-cy-kind": "Image"
        },
        "depth": {
          "type": "string"
        },
        "project": {
          "type": "string"
        }
      },
      "required": [
        "render"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "suggest_camera_move",
    "name": "Read the camera move",
    "description": "Compare the start and end cameras of a 3D panel and name the move (push in, truck, pan, tilt, crane, zoom, arc...) with its amplitude and speed; apply = write it into the panel prompt.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "panel": {
          "type": "string"
        },
        "apply": {
          "type": "boolean",
          "default": false
        }
      },
      "required": [
        "project",
        "panel"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "cameraMove": {
          "type": "string"
        },
        "cameraAmplitude": {
          "type": "string"
        },
        "cameraSpeed": {
          "type": "string"
        }
      },
      "required": [
        "cameraMove"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "export_h3_film",
    "name": "Export a MiniMax H3 film",
    "description": "Turn the storyboard into a multi-segment MiniMax H3 film: film.json (a Timeline Director timeline: by default the panels of a sequence grouped into windows of about 20 s whose prompt describes the shots in order, overlap frames where the picture continues, identity/location/shot pictures per window), its pictures, and two ComfyUI workflows (CyTools H3 Film disk sampler, Timeline Director). The same file runs in CyTools_MiniMaxH3 on Colab.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "folder": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Target folder (replaced); default exports/h3_film/<title>."
        },
        "options": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "shortEdge": {
              "type": "integer",
              "enum": [
                384,
                448,
                512,
                544,
                576,
                640,
                704,
                768
              ],
              "description": "Short edge of the canvas; the other side follows the storyboard aspect (multiples of 32)."
            },
            "width": {
              "type": "integer",
              "minimum": 0,
              "maximum": 2560,
              "description": "Explicit width (with height); 0 = from shortEdge."
            },
            "height": {
              "type": "integer",
              "minimum": 0,
              "maximum": 2560
            },
            "grouping": {
              "type": "string",
              "enum": [
                "panel",
                "sequence",
                "film"
              ],
              "description": "panel: one segment per panel; sequence (default): consecutive panels of a sequence share segments of about maxSegmentSeconds, H3 cutting between their shots; film: the same across sequences."
            },
            "maxSegmentSeconds": {
              "type": "number",
              "minimum": 2,
              "maximum": 149,
              "description": "Longest grouped segment."
            },
            "maxShotsPerSegment": {
              "type": "integer",
              "minimum": 0,
              "description": "Most shots in a grouped segment; 0 = no limit."
            },
            "shotText": {
              "type": "string",
              "maxLength": 2000,
              "description": "Shot header in a grouped segment; {shot}, {start}, {end}, {title}."
            },
            "dialogueText": {
              "type": "string",
              "maxLength": 2000,
              "description": "A line; {name}, {how} (\" (off screen)\"), {line}."
            },
            "soundText": {
              "type": "string",
              "maxLength": 2000,
              "description": "A shot's sound; {text}. Empty leaves it out."
            },
            "musicText": {
              "type": "string",
              "maxLength": 2000,
              "description": "A shot's music; {text}. Empty leaves it out."
            },
            "overlapFrames": {
              "type": "integer",
              "enum": [
                0,
                1,
                5,
                22,
                39,
                56,
                73
              ],
              "description": "Frames each segment re-generates from the previous one (continuity); removed at assembly."
            },
            "overlapOnCuts": {
              "type": "boolean",
              "description": "Also carry continuity across plain cuts (same scene)."
            },
            "overlapOnFades": {
              "type": "boolean",
              "description": "Also carry continuity across fades to/from black."
            },
            "globalPrompt": {
              "type": "string",
              "maxLength": 8000,
              "description": "Text added to every segment."
            },
            "includeStyle": {
              "type": "boolean"
            },
            "includeDescription": {
              "type": "boolean"
            },
            "referenceNote": {
              "type": "string",
              "maxLength": 4000
            },
            "continuityText": {
              "type": "string",
              "maxLength": 4000,
              "description": "Sentence for carried frames; {frames}, {seconds}."
            },
            "identityScope": {
              "type": "string",
              "enum": [
                "panel",
                "film"
              ],
              "description": "Identity pictures of the characters a panel uses, or of every character in every segment."
            },
            "identityText": {
              "type": "string",
              "maxLength": 2000,
              "description": "{n}, {name}, {description}"
            },
            "identityPictures": {
              "type": "integer",
              "minimum": 1,
              "maximum": 6,
              "description": "Pictures of each character sent per segment (the first ones of the item)."
            },
            "identityMoreText": {
              "type": "string",
              "maxLength": 2000,
              "description": "Sentence of the 2nd, 3rd... picture of a character."
            },
            "shotPictures": {
              "type": "string",
              "enum": [
                "main",
                "all",
                "none"
              ],
              "description": "The panel's own pictures: the main one (layout render first), all, or none."
            },
            "layoutText": {
              "type": "string",
              "maxLength": 2000
            },
            "sketchText": {
              "type": "string",
              "maxLength": 2000
            },
            "firstText": {
              "type": "string",
              "maxLength": 2000
            },
            "lastText": {
              "type": "string",
              "maxLength": 2000
            },
            "keyframeText": {
              "type": "string",
              "maxLength": 2000,
              "description": "{n}, {time}"
            },
            "referenceText": {
              "type": "string",
              "maxLength": 2000
            },
            "includeLocations": {
              "type": "boolean"
            },
            "locationText": {
              "type": "string",
              "maxLength": 2000
            },
            "includeObjects": {
              "type": "boolean"
            },
            "objectText": {
              "type": "string",
              "maxLength": 2000
            },
            "includeStyles": {
              "type": "boolean"
            },
            "styleText": {
              "type": "string",
              "maxLength": 2000
            },
            "includeSound": {
              "type": "boolean"
            },
            "includeVideos": {
              "type": "boolean",
              "description": "Library items of kind video used by the panel become <Video N> references of its segment (3 at most)."
            },
            "videoText": {
              "type": "string",
              "maxLength": 2000,
              "description": "{n}, {name}, {description}"
            },
            "includeVoices": {
              "type": "boolean",
              "description": "An audio file among a character's files becomes its voice (<Audio N>) in the segments where it appears."
            },
            "voiceText": {
              "type": "string",
              "maxLength": 2000
            },
            "includeAudio": {
              "type": "boolean",
              "description": "Library items of kind audio used by the panel become <Audio N>."
            },
            "audioText": {
              "type": "string",
              "maxLength": 2000
            },
            "videoSound": {
              "type": "boolean",
              "description": "Also give the reference videos' own sound as <Audio N>."
            },
            "videoSoundText": {
              "type": "string",
              "maxLength": 2000,
              "description": "{n}, {video}, {name}"
            },
            "maxReferenceSeconds": {
              "type": "number",
              "minimum": 2,
              "maximum": 15,
              "description": "Longer videos and sounds are cut to this length."
            },
            "secondPass": {
              "type": "boolean",
              "description": "SelfLift two-stage sampling (low-res steps, latent upscale, high-res steps)."
            },
            "secondPassModel": {
              "type": "string",
              "maxLength": 300,
              "description": "Latent upscaler file name."
            },
            "secondPassHighSteps": {
              "type": "integer",
              "minimum": 1,
              "maximum": 50
            },
            "controlPatchModel": {
              "type": "string",
              "maxLength": 300,
              "description": "Fun ControlNet file loaded by the ComfyUI workflow written next to film.json (films with control videos)."
            },
            "generatedAudio": {
              "type": "boolean",
              "description": "Generate sound with the picture (off = silent film)."
            },
            "depthControl": {
              "type": "string",
              "enum": [
                "off",
                "indicative",
                "guided",
                "strict",
                "custom"
              ],
              "description": "Depth video of the panels staged in 3D as Fun ControlNet control: indicative (0.35, first 35 % of the steps, strong blur), guided (0.6, medium blur), strict (1.0, sharp), custom."
            },
            "controlStrength": {
              "type": "number",
              "minimum": 0.05,
              "maximum": 2
            },
            "controlEnd": {
              "type": "number",
              "minimum": 0.05,
              "maximum": 1,
              "description": "Share of the steps it applies to."
            },
            "controlBlur": {
              "type": "string",
              "enum": [
                "none",
                "medium",
                "strong"
              ]
            },
            "controlSource": {
              "type": "string",
              "enum": [
                "auto",
                "depth",
                "pose",
                "overlay"
              ],
              "description": "Control video: depth of the set, OpenPose pose of the characters, auto (pose when a character is in frame), or the pose drawn over the depth (experimental)."
            },
            "poseFeet": {
              "type": "boolean",
              "description": "Draw the feet (OpenPose BODY_25: heel, big toe, small toe) in the pose control."
            },
            "poseHands": {
              "type": "boolean",
              "description": "Draw the hands (OpenPose hand model, 21 points) in the pose control when they are large enough on screen."
            }
          }
        },
        "workflows": {
          "type": "boolean",
          "default": true
        },
        "save_options": {
          "type": "boolean",
          "default": true,
          "description": "Remember these options in the project."
        }
      },
      "required": [
        "project"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "segments": {
          "type": "array"
        },
        "frames": {
          "type": "integer"
        },
        "seconds": {
          "type": "number"
        },
        "width": {
          "type": "integer"
        },
        "height": {
          "type": "integer"
        },
        "warnings": {
          "type": "array"
        },
        "folder": {
          "type": "string",
          "x-cy-kind": "Directory"
        },
        "file": {
          "type": "string"
        },
        "files": {
          "type": "array"
        },
        "globalPrompt": {
          "type": "string"
        },
        "options": {
          "type": "object"
        }
      },
      "required": [
        "segments",
        "frames"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": true
  },
  {
    "id": "export_h3_workflow",
    "name": "Convert to a MiniMax H3 workflow",
    "description": "Convert the storyboard into a CyTools_MiniMaxH3 workflow (workflow.json + media/): one H3 generation per panel with its first/last frame, keyframe guides and references (characters, layout, locations, videos, voices, sounds), chaining, prompts in the H3 layout, durations trimmed to the panels, and a final edit with the storyboard transitions. Run it with run_workflow in CyTools_MiniMaxH3.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "folder": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Target folder (replaced); default exports/h3_workflow/<title>."
        },
        "options": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "shortEdge": {
              "type": "integer",
              "enum": [
                384,
                448,
                512,
                544,
                576,
                640,
                704,
                768
              ]
            },
            "width": {
              "type": "integer",
              "minimum": 0,
              "maximum": 2560
            },
            "height": {
              "type": "integer",
              "minimum": 0,
              "maximum": 2560
            },
            "seed": {
              "type": "integer",
              "minimum": 0,
              "maximum": 9007199254740991
            },
            "seedPolicy": {
              "type": "string",
              "enum": [
                "fixed",
                "increment",
                "random"
              ]
            },
            "steps": {
              "type": "integer",
              "minimum": 0,
              "maximum": 100,
              "description": "0 = the Tool default."
            },
            "acceleration": {
              "type": "string",
              "enum": [
                "none",
                "turbo4",
                "turbo8"
              ],
              "description": "Turbo LoRA for shots without references."
            },
            "referenceAcceleration": {
              "type": "string",
              "enum": [
                "none",
                "turbo4"
              ],
              "description": "Turbo LoRA for shots with references (H3 has no 8-step one for them)."
            },
            "chain": {
              "type": "string",
              "enum": [
                "crossfades",
                "always",
                "never"
              ],
              "description": "Start a shot on the last frame of the previous one: after crossfades, always, never."
            },
            "longPanels": {
              "type": "string",
              "enum": [
                "split",
                "clamp"
              ],
              "description": "Panels over 15 s: chained parts, or 15 s."
            },
            "shortPanels": {
              "type": "string",
              "enum": [
                "trim",
                "extend"
              ],
              "description": "Panels under 4 s: generate 4 s and trim, or keep 4 s."
            },
            "exactDurations": {
              "type": "boolean",
              "description": "Trim each shot to its panel duration (H3 rounds up to 5 + 17n frames)."
            },
            "layoutUse": {
              "type": "string",
              "enum": [
                "reference",
                "first_frame",
                "none"
              ],
              "description": "The 2D/3D layout render: a reference picture, the first frame, or unused."
            },
            "identityScope": {
              "type": "string",
              "enum": [
                "panel",
                "film"
              ]
            },
            "includeLocations": {
              "type": "boolean"
            },
            "includeObjects": {
              "type": "boolean"
            },
            "includeStyles": {
              "type": "boolean"
            },
            "includeSketches": {
              "type": "boolean"
            },
            "includeVideos": {
              "type": "boolean"
            },
            "videoSound": {
              "type": "boolean"
            },
            "includeVoices": {
              "type": "boolean"
            },
            "includeAudio": {
              "type": "boolean"
            },
            "maxReferenceSeconds": {
              "type": "number",
              "minimum": 2,
              "maximum": 15
            },
            "includeStyle": {
              "type": "boolean"
            },
            "globalPrompt": {
              "type": "string",
              "maxLength": 8000
            },
            "promptLayout": {
              "type": "string",
              "enum": [
                "auto",
                "structured",
                "integrated"
              ],
              "description": "H3 prompt layout; auto = structured when characters are defined by pictures."
            },
            "layoutText": {
              "type": "string",
              "maxLength": 2000
            },
            "sketchText": {
              "type": "string",
              "maxLength": 2000
            },
            "referenceText": {
              "type": "string",
              "maxLength": 2000
            },
            "locationText": {
              "type": "string",
              "maxLength": 2000
            },
            "objectText": {
              "type": "string",
              "maxLength": 2000
            },
            "styleText": {
              "type": "string",
              "maxLength": 2000
            },
            "videoText": {
              "type": "string",
              "maxLength": 2000
            },
            "audioText": {
              "type": "string",
              "maxLength": 2000
            },
            "continuedText": {
              "type": "string",
              "maxLength": 2000
            },
            "depthControl": {
              "type": "string",
              "enum": [
                "off",
                "indicative",
                "guided",
                "strict",
                "custom"
              ],
              "description": "Depth video of the panels staged in 3D as Fun ControlNet control: indicative (0.35, first 35 % of the steps, strong blur), guided (0.6, medium blur), strict (1.0, sharp), custom."
            },
            "controlStrength": {
              "type": "number",
              "minimum": 0.05,
              "maximum": 2
            },
            "controlEnd": {
              "type": "number",
              "minimum": 0.05,
              "maximum": 1,
              "description": "Share of the steps it applies to."
            },
            "controlBlur": {
              "type": "string",
              "enum": [
                "none",
                "medium",
                "strong"
              ]
            },
            "controlSource": {
              "type": "string",
              "enum": [
                "auto",
                "depth",
                "pose",
                "overlay"
              ],
              "description": "Control video: depth of the set, OpenPose pose of the characters, auto (pose when a character is in frame), or the pose drawn over the depth (experimental)."
            },
            "poseFeet": {
              "type": "boolean",
              "description": "Draw the feet (OpenPose BODY_25: heel, big toe, small toe) in the pose control."
            },
            "poseHands": {
              "type": "boolean",
              "description": "Draw the hands (OpenPose hand model, 21 points) in the pose control when they are large enough on screen."
            },
            "controlVersion": {
              "type": "string",
              "enum": [
                "2.0",
                "1.0"
              ],
              "description": "Fun ControlNet Union version."
            }
          }
        },
        "save_options": {
          "type": "boolean",
          "default": true
        }
      },
      "required": [
        "project"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "shots": {
          "type": "array"
        },
        "width": {
          "type": "integer"
        },
        "height": {
          "type": "integer"
        },
        "seconds": {
          "type": "number"
        },
        "generations": {
          "type": "integer"
        },
        "steps": {
          "type": "integer"
        },
        "warnings": {
          "type": "array"
        },
        "folder": {
          "type": "string",
          "x-cy-kind": "Directory"
        },
        "file": {
          "type": "string",
          "x-cy-kind": "File"
        },
        "workflow": {
          "type": "object"
        }
      },
      "required": [
        "shots"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": true
  },
  {
    "id": "preview_h3_workflow",
    "name": "Preview the MiniMax H3 workflow",
    "description": "The shots, generations, trims, references and prompts the conversion would produce, and the workflow itself, without writing.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "options": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "shortEdge": {
              "type": "integer",
              "enum": [
                384,
                448,
                512,
                544,
                576,
                640,
                704,
                768
              ]
            },
            "width": {
              "type": "integer",
              "minimum": 0,
              "maximum": 2560
            },
            "height": {
              "type": "integer",
              "minimum": 0,
              "maximum": 2560
            },
            "seed": {
              "type": "integer",
              "minimum": 0,
              "maximum": 9007199254740991
            },
            "seedPolicy": {
              "type": "string",
              "enum": [
                "fixed",
                "increment",
                "random"
              ]
            },
            "steps": {
              "type": "integer",
              "minimum": 0,
              "maximum": 100,
              "description": "0 = the Tool default."
            },
            "acceleration": {
              "type": "string",
              "enum": [
                "none",
                "turbo4",
                "turbo8"
              ],
              "description": "Turbo LoRA for shots without references."
            },
            "referenceAcceleration": {
              "type": "string",
              "enum": [
                "none",
                "turbo4"
              ],
              "description": "Turbo LoRA for shots with references (H3 has no 8-step one for them)."
            },
            "chain": {
              "type": "string",
              "enum": [
                "crossfades",
                "always",
                "never"
              ],
              "description": "Start a shot on the last frame of the previous one: after crossfades, always, never."
            },
            "longPanels": {
              "type": "string",
              "enum": [
                "split",
                "clamp"
              ],
              "description": "Panels over 15 s: chained parts, or 15 s."
            },
            "shortPanels": {
              "type": "string",
              "enum": [
                "trim",
                "extend"
              ],
              "description": "Panels under 4 s: generate 4 s and trim, or keep 4 s."
            },
            "exactDurations": {
              "type": "boolean",
              "description": "Trim each shot to its panel duration (H3 rounds up to 5 + 17n frames)."
            },
            "layoutUse": {
              "type": "string",
              "enum": [
                "reference",
                "first_frame",
                "none"
              ],
              "description": "The 2D/3D layout render: a reference picture, the first frame, or unused."
            },
            "identityScope": {
              "type": "string",
              "enum": [
                "panel",
                "film"
              ]
            },
            "includeLocations": {
              "type": "boolean"
            },
            "includeObjects": {
              "type": "boolean"
            },
            "includeStyles": {
              "type": "boolean"
            },
            "includeSketches": {
              "type": "boolean"
            },
            "includeVideos": {
              "type": "boolean"
            },
            "videoSound": {
              "type": "boolean"
            },
            "includeVoices": {
              "type": "boolean"
            },
            "includeAudio": {
              "type": "boolean"
            },
            "maxReferenceSeconds": {
              "type": "number",
              "minimum": 2,
              "maximum": 15
            },
            "includeStyle": {
              "type": "boolean"
            },
            "globalPrompt": {
              "type": "string",
              "maxLength": 8000
            },
            "promptLayout": {
              "type": "string",
              "enum": [
                "auto",
                "structured",
                "integrated"
              ],
              "description": "H3 prompt layout; auto = structured when characters are defined by pictures."
            },
            "layoutText": {
              "type": "string",
              "maxLength": 2000
            },
            "sketchText": {
              "type": "string",
              "maxLength": 2000
            },
            "referenceText": {
              "type": "string",
              "maxLength": 2000
            },
            "locationText": {
              "type": "string",
              "maxLength": 2000
            },
            "objectText": {
              "type": "string",
              "maxLength": 2000
            },
            "styleText": {
              "type": "string",
              "maxLength": 2000
            },
            "videoText": {
              "type": "string",
              "maxLength": 2000
            },
            "audioText": {
              "type": "string",
              "maxLength": 2000
            },
            "continuedText": {
              "type": "string",
              "maxLength": 2000
            },
            "depthControl": {
              "type": "string",
              "enum": [
                "off",
                "indicative",
                "guided",
                "strict",
                "custom"
              ],
              "description": "Depth video of the panels staged in 3D as Fun ControlNet control: indicative (0.35, first 35 % of the steps, strong blur), guided (0.6, medium blur), strict (1.0, sharp), custom."
            },
            "controlStrength": {
              "type": "number",
              "minimum": 0.05,
              "maximum": 2
            },
            "controlEnd": {
              "type": "number",
              "minimum": 0.05,
              "maximum": 1,
              "description": "Share of the steps it applies to."
            },
            "controlBlur": {
              "type": "string",
              "enum": [
                "none",
                "medium",
                "strong"
              ]
            },
            "controlSource": {
              "type": "string",
              "enum": [
                "auto",
                "depth",
                "pose",
                "overlay"
              ],
              "description": "Control video: depth of the set, OpenPose pose of the characters, auto (pose when a character is in frame), or the pose drawn over the depth (experimental)."
            },
            "poseFeet": {
              "type": "boolean",
              "description": "Draw the feet (OpenPose BODY_25: heel, big toe, small toe) in the pose control."
            },
            "poseHands": {
              "type": "boolean",
              "description": "Draw the hands (OpenPose hand model, 21 points) in the pose control when they are large enough on screen."
            },
            "controlVersion": {
              "type": "string",
              "enum": [
                "2.0",
                "1.0"
              ],
              "description": "Fun ControlNet Union version."
            }
          }
        }
      },
      "required": [
        "project"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "shots": {
          "type": "array"
        },
        "width": {
          "type": "integer"
        },
        "height": {
          "type": "integer"
        },
        "seconds": {
          "type": "number"
        },
        "generations": {
          "type": "integer"
        },
        "steps": {
          "type": "integer"
        },
        "warnings": {
          "type": "array"
        },
        "folder": {
          "type": "string",
          "x-cy-kind": "Directory"
        },
        "file": {
          "type": "string",
          "x-cy-kind": "File"
        },
        "workflow": {
          "type": "object"
        }
      },
      "required": [
        "shots"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "preview_h3_film",
    "name": "Preview a MiniMax H3 film",
    "description": "Segments, frame windows, pictures and prompts the export would produce, without writing anything.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "options": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "shortEdge": {
              "type": "integer",
              "enum": [
                384,
                448,
                512,
                544,
                576,
                640,
                704,
                768
              ],
              "description": "Short edge of the canvas; the other side follows the storyboard aspect (multiples of 32)."
            },
            "width": {
              "type": "integer",
              "minimum": 0,
              "maximum": 2560,
              "description": "Explicit width (with height); 0 = from shortEdge."
            },
            "height": {
              "type": "integer",
              "minimum": 0,
              "maximum": 2560
            },
            "grouping": {
              "type": "string",
              "enum": [
                "panel",
                "sequence",
                "film"
              ],
              "description": "panel: one segment per panel; sequence (default): consecutive panels of a sequence share segments of about maxSegmentSeconds, H3 cutting between their shots; film: the same across sequences."
            },
            "maxSegmentSeconds": {
              "type": "number",
              "minimum": 2,
              "maximum": 149,
              "description": "Longest grouped segment."
            },
            "maxShotsPerSegment": {
              "type": "integer",
              "minimum": 0,
              "description": "Most shots in a grouped segment; 0 = no limit."
            },
            "shotText": {
              "type": "string",
              "maxLength": 2000,
              "description": "Shot header in a grouped segment; {shot}, {start}, {end}, {title}."
            },
            "dialogueText": {
              "type": "string",
              "maxLength": 2000,
              "description": "A line; {name}, {how} (\" (off screen)\"), {line}."
            },
            "soundText": {
              "type": "string",
              "maxLength": 2000,
              "description": "A shot's sound; {text}. Empty leaves it out."
            },
            "musicText": {
              "type": "string",
              "maxLength": 2000,
              "description": "A shot's music; {text}. Empty leaves it out."
            },
            "overlapFrames": {
              "type": "integer",
              "enum": [
                0,
                1,
                5,
                22,
                39,
                56,
                73
              ],
              "description": "Frames each segment re-generates from the previous one (continuity); removed at assembly."
            },
            "overlapOnCuts": {
              "type": "boolean",
              "description": "Also carry continuity across plain cuts (same scene)."
            },
            "overlapOnFades": {
              "type": "boolean",
              "description": "Also carry continuity across fades to/from black."
            },
            "globalPrompt": {
              "type": "string",
              "maxLength": 8000,
              "description": "Text added to every segment."
            },
            "includeStyle": {
              "type": "boolean"
            },
            "includeDescription": {
              "type": "boolean"
            },
            "referenceNote": {
              "type": "string",
              "maxLength": 4000
            },
            "continuityText": {
              "type": "string",
              "maxLength": 4000,
              "description": "Sentence for carried frames; {frames}, {seconds}."
            },
            "identityScope": {
              "type": "string",
              "enum": [
                "panel",
                "film"
              ],
              "description": "Identity pictures of the characters a panel uses, or of every character in every segment."
            },
            "identityText": {
              "type": "string",
              "maxLength": 2000,
              "description": "{n}, {name}, {description}"
            },
            "identityPictures": {
              "type": "integer",
              "minimum": 1,
              "maximum": 6,
              "description": "Pictures of each character sent per segment (the first ones of the item)."
            },
            "identityMoreText": {
              "type": "string",
              "maxLength": 2000,
              "description": "Sentence of the 2nd, 3rd... picture of a character."
            },
            "shotPictures": {
              "type": "string",
              "enum": [
                "main",
                "all",
                "none"
              ],
              "description": "The panel's own pictures: the main one (layout render first), all, or none."
            },
            "layoutText": {
              "type": "string",
              "maxLength": 2000
            },
            "sketchText": {
              "type": "string",
              "maxLength": 2000
            },
            "firstText": {
              "type": "string",
              "maxLength": 2000
            },
            "lastText": {
              "type": "string",
              "maxLength": 2000
            },
            "keyframeText": {
              "type": "string",
              "maxLength": 2000,
              "description": "{n}, {time}"
            },
            "referenceText": {
              "type": "string",
              "maxLength": 2000
            },
            "includeLocations": {
              "type": "boolean"
            },
            "locationText": {
              "type": "string",
              "maxLength": 2000
            },
            "includeObjects": {
              "type": "boolean"
            },
            "objectText": {
              "type": "string",
              "maxLength": 2000
            },
            "includeStyles": {
              "type": "boolean"
            },
            "styleText": {
              "type": "string",
              "maxLength": 2000
            },
            "includeSound": {
              "type": "boolean"
            },
            "includeVideos": {
              "type": "boolean",
              "description": "Library items of kind video used by the panel become <Video N> references of its segment (3 at most)."
            },
            "videoText": {
              "type": "string",
              "maxLength": 2000,
              "description": "{n}, {name}, {description}"
            },
            "includeVoices": {
              "type": "boolean",
              "description": "An audio file among a character's files becomes its voice (<Audio N>) in the segments where it appears."
            },
            "voiceText": {
              "type": "string",
              "maxLength": 2000
            },
            "includeAudio": {
              "type": "boolean",
              "description": "Library items of kind audio used by the panel become <Audio N>."
            },
            "audioText": {
              "type": "string",
              "maxLength": 2000
            },
            "videoSound": {
              "type": "boolean",
              "description": "Also give the reference videos' own sound as <Audio N>."
            },
            "videoSoundText": {
              "type": "string",
              "maxLength": 2000,
              "description": "{n}, {video}, {name}"
            },
            "maxReferenceSeconds": {
              "type": "number",
              "minimum": 2,
              "maximum": 15,
              "description": "Longer videos and sounds are cut to this length."
            },
            "secondPass": {
              "type": "boolean",
              "description": "SelfLift two-stage sampling (low-res steps, latent upscale, high-res steps)."
            },
            "secondPassModel": {
              "type": "string",
              "maxLength": 300,
              "description": "Latent upscaler file name."
            },
            "secondPassHighSteps": {
              "type": "integer",
              "minimum": 1,
              "maximum": 50
            },
            "controlPatchModel": {
              "type": "string",
              "maxLength": 300,
              "description": "Fun ControlNet file loaded by the ComfyUI workflow written next to film.json (films with control videos)."
            },
            "generatedAudio": {
              "type": "boolean",
              "description": "Generate sound with the picture (off = silent film)."
            },
            "depthControl": {
              "type": "string",
              "enum": [
                "off",
                "indicative",
                "guided",
                "strict",
                "custom"
              ],
              "description": "Depth video of the panels staged in 3D as Fun ControlNet control: indicative (0.35, first 35 % of the steps, strong blur), guided (0.6, medium blur), strict (1.0, sharp), custom."
            },
            "controlStrength": {
              "type": "number",
              "minimum": 0.05,
              "maximum": 2
            },
            "controlEnd": {
              "type": "number",
              "minimum": 0.05,
              "maximum": 1,
              "description": "Share of the steps it applies to."
            },
            "controlBlur": {
              "type": "string",
              "enum": [
                "none",
                "medium",
                "strong"
              ]
            },
            "controlSource": {
              "type": "string",
              "enum": [
                "auto",
                "depth",
                "pose",
                "overlay"
              ],
              "description": "Control video: depth of the set, OpenPose pose of the characters, auto (pose when a character is in frame), or the pose drawn over the depth (experimental)."
            },
            "poseFeet": {
              "type": "boolean",
              "description": "Draw the feet (OpenPose BODY_25: heel, big toe, small toe) in the pose control."
            },
            "poseHands": {
              "type": "boolean",
              "description": "Draw the hands (OpenPose hand model, 21 points) in the pose control when they are large enough on screen."
            }
          }
        }
      },
      "required": [
        "project"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "segments": {
          "type": "array"
        },
        "frames": {
          "type": "integer"
        },
        "seconds": {
          "type": "number"
        },
        "width": {
          "type": "integer"
        },
        "height": {
          "type": "integer"
        },
        "warnings": {
          "type": "array"
        },
        "folder": {
          "type": "string",
          "x-cy-kind": "Directory"
        },
        "file": {
          "type": "string"
        },
        "files": {
          "type": "array"
        },
        "globalPrompt": {
          "type": "string"
        },
        "options": {
          "type": "object"
        }
      },
      "required": [
        "segments",
        "frames"
      ]
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "plan_images",
    "name": "Plan pictures",
    "description": "The requests a recipe would send to the image model (prompts, reference pictures, sizes, seeds), without generating anything.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project (needed by every recipe except free)."
        },
        "recipe": {
          "type": "string",
          "enum": [
            "character",
            "location",
            "panel",
            "free"
          ],
          "default": "free",
          "description": "character: views of a library character; location: views of a place, empty or with a character; panel: the picture of a shot; free: any prompt."
        },
        "item": {
          "type": "string",
          "maxLength": 80,
          "description": "Library item id (character or location recipe)."
        },
        "panel": {
          "type": "string",
          "maxLength": 80,
          "description": "Panel id (panel recipe)."
        },
        "views": {
          "type": "array",
          "maxItems": 40,
          "items": {
            "type": "string",
            "maxLength": 60
          },
          "description": "View keys to render; default: the views switched on in the options."
        },
        "character": {
          "type": "string",
          "maxLength": 80,
          "description": "Character id placed in the location (location recipe)."
        },
        "prompt": {
          "type": "string",
          "maxLength": 8000,
          "description": "Text of the free recipe."
        },
        "references": {
          "type": "array",
          "maxItems": 16,
          "items": {
            "type": "string",
            "maxLength": 4096
          },
          "description": "Free recipe: picture files or library item ids used as references (none = from the text)."
        },
        "format": {
          "type": "string",
          "enum": [
            "project",
            "1:1",
            "3:4",
            "4:3",
            "2:3",
            "3:2",
            "9:16",
            "16:9",
            "21:9",
            "2.39:1"
          ]
        },
        "extra": {
          "type": "string",
          "maxLength": 2000,
          "description": "Added to every prompt of the recipe."
        },
        "extras": {
          "type": "string",
          "maxLength": 80,
          "description": "Panel recipe: character id that every mannequin of the staging without a reference stands for (a crowd of the same character)."
        },
        "label": {
          "type": "string",
          "maxLength": 120
        },
        "options": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "model": {
              "type": "string",
              "maxLength": 80,
              "description": "Image model for pictures from references (\"\" = the default installed one). See image_engine_status."
            },
            "textModel": {
              "type": "string",
              "maxLength": 80,
              "description": "Image model for pictures from a text alone."
            },
            "steps": {
              "type": "integer",
              "minimum": 0,
              "maximum": 100,
              "description": "0 = the model default."
            },
            "guidance": {
              "type": "number",
              "minimum": 0,
              "maximum": 20,
              "description": "0 = the model default."
            },
            "fast": {
              "type": "boolean",
              "description": "Few-step LoRA when the model has one."
            },
            "megapixels": {
              "type": "number",
              "minimum": 0.25,
              "maximum": 4
            },
            "count": {
              "type": "integer",
              "minimum": 1,
              "maximum": 16,
              "description": "Pictures per view."
            },
            "seed": {
              "type": "integer",
              "minimum": 0,
              "maximum": 2147483647
            },
            "randomSeed": {
              "type": "boolean",
              "description": "false: `seed`, seed + 1... are used, for reproducible pictures."
            },
            "negative": {
              "type": "string",
              "maxLength": 4000
            },
            "includeStyle": {
              "type": "boolean"
            },
            "loras": {
              "type": "array",
              "maxItems": 8,
              "description": "LoRA files applied to the model, in order; names inside data/models/comfyui/loras (see image_engine_status). A LoRA belongs to one model family.",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "file"
                ],
                "properties": {
                  "file": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 255
                  },
                  "strength": {
                    "type": "number",
                    "minimum": -4,
                    "maximum": 4,
                    "default": 1.0
                  },
                  "on": {
                    "type": "boolean",
                    "default": true
                  }
                }
              }
            },
            "keepLoadedMinutes": {
              "type": "integer",
              "minimum": 0,
              "maximum": 1440,
              "description": "The model stays in memory this long after the last picture; 0 = until unloaded."
            },
            "server": {
              "type": "string",
              "maxLength": 500,
              "description": "Address of another ComfyUI to render on (Colab tunnel); \"\" = the private engine of the application."
            },
            "characterViews": {
              "type": "array",
              "maxItems": 40,
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "key",
                  "text"
                ],
                "properties": {
                  "key": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 60
                  },
                  "text": {
                    "type": "string",
                    "maxLength": 2000
                  },
                  "on": {
                    "type": "boolean"
                  },
                  "format": {
                    "type": "string",
                    "enum": [
                      "project",
                      "1:1",
                      "3:4",
                      "4:3",
                      "2:3",
                      "3:2",
                      "9:16",
                      "16:9",
                      "21:9",
                      "2.39:1"
                    ]
                  }
                }
              }
            },
            "locationViews": {
              "type": "array",
              "maxItems": 40,
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "key",
                  "text"
                ],
                "properties": {
                  "key": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 60
                  },
                  "text": {
                    "type": "string",
                    "maxLength": 2000
                  },
                  "on": {
                    "type": "boolean"
                  },
                  "format": {
                    "type": "string",
                    "enum": [
                      "project",
                      "1:1",
                      "3:4",
                      "4:3",
                      "2:3",
                      "3:2",
                      "9:16",
                      "16:9",
                      "21:9",
                      "2.39:1"
                    ]
                  }
                }
              }
            },
            "characterText": {
              "type": "string",
              "maxLength": 4000
            },
            "characterFromText": {
              "type": "string",
              "maxLength": 4000
            },
            "locationText": {
              "type": "string",
              "maxLength": 4000
            },
            "locationFromText": {
              "type": "string",
              "maxLength": 4000
            },
            "locationWithCharacterText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelFramingText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelCharacterText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelExtrasText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelUnknownText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelCrowdText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelLocationText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelFormat": {
              "type": "string",
              "enum": [
                "project",
                "1:1",
                "3:4",
                "4:3",
                "2:3",
                "3:2",
                "9:16",
                "16:9",
                "21:9",
                "2.39:1"
              ]
            },
            "panelGuide": {
              "type": "string",
              "enum": [
                "auto",
                "control",
                "layout",
                "both",
                "none"
              ],
              "description": "How a 3D-staged shot gets its framing: control (depth or pose of the staging through the ControlNet of the model), layout (the staging render as a picture), both, none; auto = control when the ControlNet is installed, else layout."
            },
            "panelControlSource": {
              "type": "string",
              "enum": [
                "depth",
                "pose",
                "overlay"
              ]
            },
            "panelControlStrength": {
              "type": "number",
              "exclusiveMinimum": 0,
              "maximum": 2
            },
            "panelControlEnd": {
              "type": "number",
              "exclusiveMinimum": 0,
              "maximum": 1,
              "description": "Share of the steps during which the control applies."
            },
            "panelControlBlur": {
              "type": "string",
              "enum": [
                "none",
                "medium",
                "strong"
              ]
            },
            "panelCharacterPictures": {
              "type": "integer",
              "minimum": 1,
              "maximum": 6,
              "description": "Pictures of each character sent for a shot or a place: its first picture, then its generated views (full body first)."
            },
            "freeFormat": {
              "type": "string",
              "enum": [
                "project",
                "1:1",
                "3:4",
                "4:3",
                "2:3",
                "3:2",
                "9:16",
                "16:9",
                "21:9",
                "2.39:1"
              ]
            }
          }
        }
      },
      "required": [],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "additionalProperties": true
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "generate_images",
    "name": "Generate pictures",
    "description": "Generate reference pictures in the application: views of a character or a place from its reference pictures (or from its description), a character placed in a place, the picture of a shot from its staging render, or a free prompt. The model stays loaded between calls. Returns the pictures with their recipe; keep=true copies them into the project and attaches them (library item files, first image of the panel).",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project (needed by every recipe except free)."
        },
        "recipe": {
          "type": "string",
          "enum": [
            "character",
            "location",
            "panel",
            "free"
          ],
          "default": "free",
          "description": "character: views of a library character; location: views of a place, empty or with a character; panel: the picture of a shot; free: any prompt."
        },
        "item": {
          "type": "string",
          "maxLength": 80,
          "description": "Library item id (character or location recipe)."
        },
        "panel": {
          "type": "string",
          "maxLength": 80,
          "description": "Panel id (panel recipe)."
        },
        "views": {
          "type": "array",
          "maxItems": 40,
          "items": {
            "type": "string",
            "maxLength": 60
          },
          "description": "View keys to render; default: the views switched on in the options."
        },
        "character": {
          "type": "string",
          "maxLength": 80,
          "description": "Character id placed in the location (location recipe)."
        },
        "prompt": {
          "type": "string",
          "maxLength": 8000,
          "description": "Text of the free recipe."
        },
        "references": {
          "type": "array",
          "maxItems": 16,
          "items": {
            "type": "string",
            "maxLength": 4096
          },
          "description": "Free recipe: picture files or library item ids used as references (none = from the text)."
        },
        "format": {
          "type": "string",
          "enum": [
            "project",
            "1:1",
            "3:4",
            "4:3",
            "2:3",
            "3:2",
            "9:16",
            "16:9",
            "21:9",
            "2.39:1"
          ]
        },
        "extra": {
          "type": "string",
          "maxLength": 2000,
          "description": "Added to every prompt of the recipe."
        },
        "extras": {
          "type": "string",
          "maxLength": 80,
          "description": "Panel recipe: character id that every mannequin of the staging without a reference stands for (a crowd of the same character)."
        },
        "label": {
          "type": "string",
          "maxLength": 120
        },
        "options": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "model": {
              "type": "string",
              "maxLength": 80,
              "description": "Image model for pictures from references (\"\" = the default installed one). See image_engine_status."
            },
            "textModel": {
              "type": "string",
              "maxLength": 80,
              "description": "Image model for pictures from a text alone."
            },
            "steps": {
              "type": "integer",
              "minimum": 0,
              "maximum": 100,
              "description": "0 = the model default."
            },
            "guidance": {
              "type": "number",
              "minimum": 0,
              "maximum": 20,
              "description": "0 = the model default."
            },
            "fast": {
              "type": "boolean",
              "description": "Few-step LoRA when the model has one."
            },
            "megapixels": {
              "type": "number",
              "minimum": 0.25,
              "maximum": 4
            },
            "count": {
              "type": "integer",
              "minimum": 1,
              "maximum": 16,
              "description": "Pictures per view."
            },
            "seed": {
              "type": "integer",
              "minimum": 0,
              "maximum": 2147483647
            },
            "randomSeed": {
              "type": "boolean",
              "description": "false: `seed`, seed + 1... are used, for reproducible pictures."
            },
            "negative": {
              "type": "string",
              "maxLength": 4000
            },
            "includeStyle": {
              "type": "boolean"
            },
            "loras": {
              "type": "array",
              "maxItems": 8,
              "description": "LoRA files applied to the model, in order; names inside data/models/comfyui/loras (see image_engine_status). A LoRA belongs to one model family.",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "file"
                ],
                "properties": {
                  "file": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 255
                  },
                  "strength": {
                    "type": "number",
                    "minimum": -4,
                    "maximum": 4,
                    "default": 1.0
                  },
                  "on": {
                    "type": "boolean",
                    "default": true
                  }
                }
              }
            },
            "keepLoadedMinutes": {
              "type": "integer",
              "minimum": 0,
              "maximum": 1440,
              "description": "The model stays in memory this long after the last picture; 0 = until unloaded."
            },
            "server": {
              "type": "string",
              "maxLength": 500,
              "description": "Address of another ComfyUI to render on (Colab tunnel); \"\" = the private engine of the application."
            },
            "characterViews": {
              "type": "array",
              "maxItems": 40,
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "key",
                  "text"
                ],
                "properties": {
                  "key": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 60
                  },
                  "text": {
                    "type": "string",
                    "maxLength": 2000
                  },
                  "on": {
                    "type": "boolean"
                  },
                  "format": {
                    "type": "string",
                    "enum": [
                      "project",
                      "1:1",
                      "3:4",
                      "4:3",
                      "2:3",
                      "3:2",
                      "9:16",
                      "16:9",
                      "21:9",
                      "2.39:1"
                    ]
                  }
                }
              }
            },
            "locationViews": {
              "type": "array",
              "maxItems": 40,
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "key",
                  "text"
                ],
                "properties": {
                  "key": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 60
                  },
                  "text": {
                    "type": "string",
                    "maxLength": 2000
                  },
                  "on": {
                    "type": "boolean"
                  },
                  "format": {
                    "type": "string",
                    "enum": [
                      "project",
                      "1:1",
                      "3:4",
                      "4:3",
                      "2:3",
                      "3:2",
                      "9:16",
                      "16:9",
                      "21:9",
                      "2.39:1"
                    ]
                  }
                }
              }
            },
            "characterText": {
              "type": "string",
              "maxLength": 4000
            },
            "characterFromText": {
              "type": "string",
              "maxLength": 4000
            },
            "locationText": {
              "type": "string",
              "maxLength": 4000
            },
            "locationFromText": {
              "type": "string",
              "maxLength": 4000
            },
            "locationWithCharacterText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelFramingText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelCharacterText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelExtrasText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelUnknownText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelCrowdText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelLocationText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelFormat": {
              "type": "string",
              "enum": [
                "project",
                "1:1",
                "3:4",
                "4:3",
                "2:3",
                "3:2",
                "9:16",
                "16:9",
                "21:9",
                "2.39:1"
              ]
            },
            "panelGuide": {
              "type": "string",
              "enum": [
                "auto",
                "control",
                "layout",
                "both",
                "none"
              ],
              "description": "How a 3D-staged shot gets its framing: control (depth or pose of the staging through the ControlNet of the model), layout (the staging render as a picture), both, none; auto = control when the ControlNet is installed, else layout."
            },
            "panelControlSource": {
              "type": "string",
              "enum": [
                "depth",
                "pose",
                "overlay"
              ]
            },
            "panelControlStrength": {
              "type": "number",
              "exclusiveMinimum": 0,
              "maximum": 2
            },
            "panelControlEnd": {
              "type": "number",
              "exclusiveMinimum": 0,
              "maximum": 1,
              "description": "Share of the steps during which the control applies."
            },
            "panelControlBlur": {
              "type": "string",
              "enum": [
                "none",
                "medium",
                "strong"
              ]
            },
            "panelCharacterPictures": {
              "type": "integer",
              "minimum": 1,
              "maximum": 6,
              "description": "Pictures of each character sent for a shot or a place: its first picture, then its generated views (full body first)."
            },
            "freeFormat": {
              "type": "string",
              "enum": [
                "project",
                "1:1",
                "3:4",
                "4:3",
                "2:3",
                "3:2",
                "9:16",
                "16:9",
                "21:9",
                "2.39:1"
              ]
            }
          }
        },
        "keep": {
          "type": "boolean",
          "default": false,
          "description": "Copy every picture into the project."
        },
        "attach": {
          "type": "boolean",
          "default": true,
          "description": "With keep: attach to the item or the panel."
        },
        "save_options": {
          "type": "boolean",
          "default": false,
          "description": "Remember the options in the project."
        }
      },
      "required": [],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "additionalProperties": true
    },
    "resourceRequirements": {
      "ramBytes": 8589934592,
      "cpuThreads": 2
    },
    "supportedBackends": [
      "comfyui"
    ],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": true,
    "exclusiveGroups": [
      "image-engine"
    ]
  },
  {
    "id": "keep_generated_image",
    "name": "Keep a generated picture",
    "description": "Copy one picture returned by generate_images into the project with its recipe, and attach it to its target.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects."
        },
        "file": {
          "type": "string",
          "x-cy-kind": "File",
          "maxLength": 4096
        },
        "attach": {
          "type": "boolean",
          "default": true
        }
      },
      "required": [
        "project",
        "file"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "additionalProperties": true
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "export_image_workflows",
    "name": "Export ComfyUI picture workflows",
    "description": "Write the ComfyUI workflow of a recipe (editor file to drop on the ComfyUI page, API prompt) and its reference pictures (folder cytools_images, to copy into ComfyUI/input): the same graph the application renders.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Project (needed by every recipe except free)."
        },
        "recipe": {
          "type": "string",
          "enum": [
            "character",
            "location",
            "panel",
            "free"
          ],
          "default": "free",
          "description": "character: views of a library character; location: views of a place, empty or with a character; panel: the picture of a shot; free: any prompt."
        },
        "item": {
          "type": "string",
          "maxLength": 80,
          "description": "Library item id (character or location recipe)."
        },
        "panel": {
          "type": "string",
          "maxLength": 80,
          "description": "Panel id (panel recipe)."
        },
        "views": {
          "type": "array",
          "maxItems": 40,
          "items": {
            "type": "string",
            "maxLength": 60
          },
          "description": "View keys to render; default: the views switched on in the options."
        },
        "character": {
          "type": "string",
          "maxLength": 80,
          "description": "Character id placed in the location (location recipe)."
        },
        "prompt": {
          "type": "string",
          "maxLength": 8000,
          "description": "Text of the free recipe."
        },
        "references": {
          "type": "array",
          "maxItems": 16,
          "items": {
            "type": "string",
            "maxLength": 4096
          },
          "description": "Free recipe: picture files or library item ids used as references (none = from the text)."
        },
        "format": {
          "type": "string",
          "enum": [
            "project",
            "1:1",
            "3:4",
            "4:3",
            "2:3",
            "3:2",
            "9:16",
            "16:9",
            "21:9",
            "2.39:1"
          ]
        },
        "extra": {
          "type": "string",
          "maxLength": 2000,
          "description": "Added to every prompt of the recipe."
        },
        "extras": {
          "type": "string",
          "maxLength": 80,
          "description": "Panel recipe: character id that every mannequin of the staging without a reference stands for (a crowd of the same character)."
        },
        "label": {
          "type": "string",
          "maxLength": 120
        },
        "options": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "model": {
              "type": "string",
              "maxLength": 80,
              "description": "Image model for pictures from references (\"\" = the default installed one). See image_engine_status."
            },
            "textModel": {
              "type": "string",
              "maxLength": 80,
              "description": "Image model for pictures from a text alone."
            },
            "steps": {
              "type": "integer",
              "minimum": 0,
              "maximum": 100,
              "description": "0 = the model default."
            },
            "guidance": {
              "type": "number",
              "minimum": 0,
              "maximum": 20,
              "description": "0 = the model default."
            },
            "fast": {
              "type": "boolean",
              "description": "Few-step LoRA when the model has one."
            },
            "megapixels": {
              "type": "number",
              "minimum": 0.25,
              "maximum": 4
            },
            "count": {
              "type": "integer",
              "minimum": 1,
              "maximum": 16,
              "description": "Pictures per view."
            },
            "seed": {
              "type": "integer",
              "minimum": 0,
              "maximum": 2147483647
            },
            "randomSeed": {
              "type": "boolean",
              "description": "false: `seed`, seed + 1... are used, for reproducible pictures."
            },
            "negative": {
              "type": "string",
              "maxLength": 4000
            },
            "includeStyle": {
              "type": "boolean"
            },
            "loras": {
              "type": "array",
              "maxItems": 8,
              "description": "LoRA files applied to the model, in order; names inside data/models/comfyui/loras (see image_engine_status). A LoRA belongs to one model family.",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "file"
                ],
                "properties": {
                  "file": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 255
                  },
                  "strength": {
                    "type": "number",
                    "minimum": -4,
                    "maximum": 4,
                    "default": 1.0
                  },
                  "on": {
                    "type": "boolean",
                    "default": true
                  }
                }
              }
            },
            "keepLoadedMinutes": {
              "type": "integer",
              "minimum": 0,
              "maximum": 1440,
              "description": "The model stays in memory this long after the last picture; 0 = until unloaded."
            },
            "server": {
              "type": "string",
              "maxLength": 500,
              "description": "Address of another ComfyUI to render on (Colab tunnel); \"\" = the private engine of the application."
            },
            "characterViews": {
              "type": "array",
              "maxItems": 40,
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "key",
                  "text"
                ],
                "properties": {
                  "key": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 60
                  },
                  "text": {
                    "type": "string",
                    "maxLength": 2000
                  },
                  "on": {
                    "type": "boolean"
                  },
                  "format": {
                    "type": "string",
                    "enum": [
                      "project",
                      "1:1",
                      "3:4",
                      "4:3",
                      "2:3",
                      "3:2",
                      "9:16",
                      "16:9",
                      "21:9",
                      "2.39:1"
                    ]
                  }
                }
              }
            },
            "locationViews": {
              "type": "array",
              "maxItems": 40,
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "key",
                  "text"
                ],
                "properties": {
                  "key": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 60
                  },
                  "text": {
                    "type": "string",
                    "maxLength": 2000
                  },
                  "on": {
                    "type": "boolean"
                  },
                  "format": {
                    "type": "string",
                    "enum": [
                      "project",
                      "1:1",
                      "3:4",
                      "4:3",
                      "2:3",
                      "3:2",
                      "9:16",
                      "16:9",
                      "21:9",
                      "2.39:1"
                    ]
                  }
                }
              }
            },
            "characterText": {
              "type": "string",
              "maxLength": 4000
            },
            "characterFromText": {
              "type": "string",
              "maxLength": 4000
            },
            "locationText": {
              "type": "string",
              "maxLength": 4000
            },
            "locationFromText": {
              "type": "string",
              "maxLength": 4000
            },
            "locationWithCharacterText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelFramingText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelCharacterText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelExtrasText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelUnknownText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelCrowdText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelLocationText": {
              "type": "string",
              "maxLength": 4000
            },
            "panelFormat": {
              "type": "string",
              "enum": [
                "project",
                "1:1",
                "3:4",
                "4:3",
                "2:3",
                "3:2",
                "9:16",
                "16:9",
                "21:9",
                "2.39:1"
              ]
            },
            "panelGuide": {
              "type": "string",
              "enum": [
                "auto",
                "control",
                "layout",
                "both",
                "none"
              ],
              "description": "How a 3D-staged shot gets its framing: control (depth or pose of the staging through the ControlNet of the model), layout (the staging render as a picture), both, none; auto = control when the ControlNet is installed, else layout."
            },
            "panelControlSource": {
              "type": "string",
              "enum": [
                "depth",
                "pose",
                "overlay"
              ]
            },
            "panelControlStrength": {
              "type": "number",
              "exclusiveMinimum": 0,
              "maximum": 2
            },
            "panelControlEnd": {
              "type": "number",
              "exclusiveMinimum": 0,
              "maximum": 1,
              "description": "Share of the steps during which the control applies."
            },
            "panelControlBlur": {
              "type": "string",
              "enum": [
                "none",
                "medium",
                "strong"
              ]
            },
            "panelCharacterPictures": {
              "type": "integer",
              "minimum": 1,
              "maximum": 6,
              "description": "Pictures of each character sent for a shot or a place: its first picture, then its generated views (full body first)."
            },
            "freeFormat": {
              "type": "string",
              "enum": [
                "project",
                "1:1",
                "3:4",
                "4:3",
                "2:3",
                "3:2",
                "9:16",
                "16:9",
                "21:9",
                "2.39:1"
              ]
            }
          }
        },
        "folder": {
          "type": "string",
          "x-cy-kind": "Directory",
          "maxLength": 4096,
          "description": "Target folder; default exports/comfyui_images in the project."
        },
        "name": {
          "type": "string",
          "maxLength": 60
        }
      },
      "required": [],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "additionalProperties": true
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "image_engine_status",
    "name": "Image engine status",
    "description": "Engine environment, models (installed, size, licence) and the model currently in memory.",
    "inputSchema": {
      "type": "object",
      "properties": {},
      "required": [],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "additionalProperties": true
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false
  },
  {
    "id": "unload_image_model",
    "name": "Unload the image model",
    "description": "Stop the image engine and give its memory back.",
    "inputSchema": {
      "type": "object",
      "properties": {},
      "required": [],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "additionalProperties": true
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false,
    "exclusiveGroups": [
      "image-engine"
    ]
  },
  {
    "id": "install_image_engine",
    "name": "Install the image engine",
    "description": "Create or repair the private engine: a Python environment with PyTorch (CUDA 13) and a pinned ComfyUI checkout, checked by import.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "cpu_only": {
          "type": "boolean",
          "default": false
        }
      },
      "required": [],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "additionalProperties": true
    },
    "resourceRequirements": {
      "ramBytes": 1073741824,
      "cpuThreads": 2,
      "diskBytes": 42949672960
    },
    "supportedBackends": [],
    "permissions": [
      "network"
    ],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": true,
    "exclusiveGroups": [
      "image-engine"
    ]
  },
  {
    "id": "install_image_model",
    "name": "Install an image model",
    "description": "Download the files of a model (resumable, size and SHA-256 checked); files shared with another model are not downloaded twice.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "model": {
          "type": "string",
          "enum": [
            "qwen-image-2.1-controlnet-int8",
            "qwen-image-2.1-int8",
            "qwen-image-2512-fp8",
            "qwen-image-edit-2511-int8"
          ]
        },
        "accept_license": {
          "type": "boolean",
          "default": true
        },
        "repair": {
          "type": "boolean",
          "default": false
        }
      },
      "required": [
        "model"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "additionalProperties": true
    },
    "resourceRequirements": {
      "ramBytes": 1073741824,
      "cpuThreads": 2,
      "diskBytes": 42949672960
    },
    "supportedBackends": [],
    "permissions": [
      "network"
    ],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": true,
    "exclusiveGroups": [
      "image-engine"
    ]
  },
  {
    "id": "verify_image_model",
    "name": "Verify an image model",
    "description": "Check every file of a model against its declared SHA-256.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "model": {
          "type": "string",
          "enum": [
            "qwen-image-2.1-controlnet-int8",
            "qwen-image-2.1-int8",
            "qwen-image-2512-fp8",
            "qwen-image-edit-2511-int8"
          ]
        }
      },
      "required": [
        "model"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "additionalProperties": true
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": true,
    "exclusiveGroups": [
      "image-engine"
    ]
  },
  {
    "id": "remove_image_model",
    "name": "Remove an image model",
    "description": "Delete the files of a model that no other installed model uses.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "model": {
          "type": "string",
          "enum": [
            "qwen-image-2.1-controlnet-int8",
            "qwen-image-2.1-int8",
            "qwen-image-2512-fp8",
            "qwen-image-edit-2511-int8"
          ]
        }
      },
      "required": [
        "model"
      ],
      "additionalProperties": false
    },
    "outputSchema": {
      "type": "object",
      "additionalProperties": true
    },
    "resourceRequirements": {
      "ramBytes": 268435456,
      "diskBytes": 536870912
    },
    "supportedBackends": [],
    "permissions": [],
    "canRunAsync": true,
    "canCancel": true,
    "supportsProgress": false,
    "exclusiveGroups": [
      "image-engine"
    ]
  }
]
```

## Host project instructions

# Creating and maintaining CyTools_Storyboard

Mesh Tools must follow Docs/MeshViewer.md: use --desktop --mesh-viewer, open completed
results in the embedded viewport, provide orbit/free mouse-keyboard navigation,
close inspection, scene presets and studio/sun lighting. Static images are insufficient.

Read Docs/SharedInstallation.md. Provide configurable local/shared download storage
and explicit versioned CUDA Toolkit selection. Keep Python private, never move
existing models or accept provider terms implicitly. Expose access-required states
and official links to users and AI clients. Ship without weights and heavy caches.

Read README.md, CyTool.json and tool.py before modifying this tool.
Read Docs/Localization.md. English is the default UI language; French is selectable
and persisted. Options includes language, theme, text scale and component licenses.
Add every new visible string to app/locales/ui.json (en/fr); never translate user data.
Read Docs/GenerationConfigurations.md. Save/load configuration and optional generation
autosave are mandatory. Use explicit configure_generation callbacks; exclude secrets.
For desktop layout these files are inside app/. Read Docs/StandaloneDelivery.md too.
Every user-facing Tool must ship a usable Dear ImGui UI, a Windows .exe and a suitable
Linux launcher. Final root: launcher(s), LISEZ-MOI.md, app/, data/, runtime/ only.
Provide guided model access/download/resume in the UI and staged GitHub updates with
rollback and data preservation. Do not claim a scaffold is a finished application.
Read CyToolsGuide.md (local copy) or CyToolsCore Docs/AgentGuide.md as the implementation contract.
Run `cytools docs` to locate the complete documentation installed with the SDK.

1. Declare every operation in CyTool.json: inputSchema, outputSchema, supportedBackends,
   permissions, resourceRequirements and actual platform support.
2. Register one handler per declared operation in create_runtime().
3. Handler signature: handler(context, parameters) -> JSON-serializable outputs.
4. Check context.cancellation during loops; use context.cancellation.sleep() for waits.
5. Create outputs using context.path('outputs/name.ext'). Never share a fixed output path.
6. Use context.progress(percent, currentStep='...') when supportsProgress is true.
7. Use runtime.register(id, handler, estimate=...) for parameter-dependent RAM/VRAM.
8. Do not implement a second scheduler, job registry, authentication system or MCP parser.
9. No UI, specific AI model or external CLI is required by the core.
10. Treat external files and executable arguments as untrusted; use argv, never shell interpolation.
11. Add real operation tests (invalid inputs, failure, cancellation, output validity).
12. Run: cytools validate CyTool.json; python -m unittest -v; python tool.py describe;
    python tool.py invoke echo --params-file params.json.
13. Document dependencies, model licenses, platform verification and limitations honestly.
14. A descriptor does not implement a backend. Do not claim a capability without code and tests.

User operation parameters cannot choose clientId, owner or a different session.
Permissions belong to the authenticated transport context. Heavy/untrusted runtimes
belong in ProcessWorker; in-process cancellation is cooperative, not forcible.
# Standalone diagnostics and model extensions

Read Docs/StandaloneDiagnosticsAndModels.md. Ship a selectable/copyable application log,
explicit planned/actual video resolution, a local model library and compatible LoRA/device
controls. Save the effective selections in generation recipes. Do not claim unsupported
CPU paths, arbitrary architecture compatibility or generic four-step acceleration.


Lire [Docs/FullOperationAccess.md](Docs/FullOperationAccess.md) : inventaire des capacités natives, parité complète des options métier entre IA et standalone, contrats de sorties composables et preuves de validation. Un formulaire simplifié ne limite pas le contrat du Tool.

Lire Docs/AutomaticInputs.md (AutomaticInputs.md depuis Docs) : chemins absolus acceptés pour les entrées locales, copie automatique privée par job, aucune copie manuelle exigée de l’IA.


## Task-owned files (SDK 0.9.0)

Read Docs/TaskFiles.md (TaskFiles.md from this Docs directory). Configure input roots and all file fields for automatic imports; AI sessions are temporary by default. FinishTask removes imported copies and generated workspaces after workers stop; export wanted results first. Standalone sessions explicitly use temporary=False.

## Operation exclusion groups (SDK 0.10.0)

Read Docs/Scheduler.md. Declare operations[].exclusiveGroups for operations that must
serialize, including conflicting model maintenance. Use the SDK queue and keep RAM/VRAM
estimates; do not add another in-handler queue for the same Runtime. Test independent
operations and hold exclusion until execution/cleanup actually stops on cancellation.
Groups are runtime-local; keep interprocess locks when separate runtimes need them.
Require SDK 0.10.0 or later; older SDKs do not enforce this field.

## Modular CyUI maintenance

Read Docs/CyUIMigration.md. cyui.py and cyui_modules/ are unmodified upstream files pinned
and hashed in cyui-source.json. Do not patch them locally; keep product adapters outside
the library. Refresh with scripts/sync_cyui.py from the exact revision. Preserve domain
behavior, isolated view state, cancellation and Undo transactions; run the app suite and
tests/test_modular_ui.py. Keep both CyUI MIT notices and the upstream license link.
