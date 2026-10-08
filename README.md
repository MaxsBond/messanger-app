# Messanger App

A messenger UI built in Unreal Engine 5.8 with UMG only. No C++ game code, no 3D scene: every screen, component, animation and data asset was created by a local AI agent that read the design from Figma and wrote it into the Unreal Editor through MCP.

This is a test project. It shows what a local agent can do when it has a bridge to both tools.

Figma design: [Messanger App](https://www.figma.com/design/ixZDtpBk5UwKQ8aWuPHvpm/Messanger-App?node-id=15-8784)


## What's in the demo

- Chat list, chat view and details panel, matching the Figma frames.
- Three layout states: list open, list collapsed, details open.
- Components: conversation row, chat bubble, link card, suggestion chip, voice message, typing indicator, recording bar, attach menu, details panel.
- Motion from the Figma "Motion" page: collapsing the chat list, opening the attach menu, recording and sending a voice message, opening the details panel, a new message moving to the top of the list.
- Working chat: rows open their conversation, suggestion chips and Enter send messages, and session messages survive switching conversations.
- A Demo button in the list header that plays incoming messages on a timer.
- Conversations are data assets (`Content/UI/Messaging/Data`), not hardcoded text.

## How it was planned

The Figma file is the spec. Each page has notes next to the frames, and the agent followed them when it built the Unreal side.

**Components.** Each Figma component maps 1:1 to a UMG User Widget with the same name. The notes say which props to expose and which widgets already exist in UE.

![Figma: UMG components](docs/figma-components.png)

**Layouts.** Three base states of the screen: chat list open, chat list collapsed, details open. In Unreal they are one widget (`WBP_MessagingLayout`) with a `State` property.

![Figma: base states](docs/figma-layouts.png)

**Motion.** Every animation has its own section with a trigger, a timeline and build notes.

![Figma motion: collapse chat list](docs/figma-motion-01-collapse-list.png)

![Figma motion: attachment menu](docs/figma-motion-02-attach-menu.png)

![Figma motion: voice message](docs/figma-motion-05-voice-message.png)

![Figma motion: details panel](docs/figma-motion-06-details-panel.png)

## Result in Unreal

`WBP_MessagingLayout` in the UMG designer. The whole tree is built from the `WBP_*` components, at the Figma frame size (905×744).

![UMG designer: WBP_MessagingLayout](docs/ue-designer.png)

The Event Graph of the same widget: each button, row and chip forwards its event to a layout function (`ToggleList`, `OpenDetails`, `SelectConversation`, ...).

![Blueprint: EventGraph overview](docs/ue-graph.png)

![Blueprint: EventGraph close-up](docs/ue-graph-detail.png)

The component widgets in `Content/UI/Messaging/Widgets`, one per Figma component:

![Content Browser: widgets](docs/ue-content-widgets.webp)

Icons imported as textures (`T_Icon_*`, sources in `SourceArt/Messaging`):

![Content Browser: icons](docs/ue-content-icons.webp)

The Reference Viewer for `WBP_MessagingLayout`: the game mode and HUD that show it, and everything it uses (data assets, icons, component widgets).

![Reference Viewer: WBP_MessagingLayout](docs/ue-reference-viewer.webp)

## How it was built

```
Figma Desktop ──figma-bridge──> AI agent ──Unreal MCP (127.0.0.1:8000)──> Unreal Editor
```

**Figma → agent.** [figma-bridge](https://github.com/MaxsBond/figma-bridge) is a local MCP server plus a Figma dev plugin. The agent reads the open file through it: node trees, layout, colors, text, exported icons. It also works on a View seat and has no rate limits.

**Agent → Unreal.** The Unreal Editor runs an MCP server (`.mcp.json`, `http://127.0.0.1:8000/mcp`) through the `ModelContextProtocol` plugin and editor toolsets (`UMGToolSet`, `EditorToolset`, `SlateInspectorToolset`, `ConfigSettingsToolset`). The agent uses them to add widgets, set properties, create Blueprint functions and events, and edit config.

<!-- TODO: link to unreal-bridge if it is published -->

Animations use a custom toolset, `UMGAnimToolset` (`PluginSource/UMGAnimToolset`): an editor plugin that creates Sequencer tracks and keys in Widget Blueprints. The built plugin is in `Plugins/UMGAnimToolset`.

**The generator scripts.** Instead of clicking through the editor, the agent wrote Python scripts that describe the UI and send it to the Unreal MCP server. They live in `SourceArt/Messaging` and can be rerun to rebuild the assets:

| Script | What it builds |
|---|---|
| `ue_mcp.py`, `ue_call.py` | Minimal client for the Unreal MCP server |
| `gen_components.py` | Component widgets (`WBP_VoiceMessage`, `WBP_TypingIndicator`, `WBP_RecordingBar`, `WBP_AttachMenu`, `WBP_DetailsPanel`) |
| `gen_layout.py` | `WBP_MessagingLayout` with all three layout states in one tree |
| `gen_layout_state.py` | State properties and `ApplyState()` |
| `gen_components_motion.py` | Component animations and event dispatchers |
| `gen_layout_motion.py` | Layout animations, chat logic, Demo button |
| `gen_data_figma.py` | Conversation data assets taken from the Figma file |
| `gen_window.py` | Window size of the packaged app (the Figma frame size) |
| `package_mac.sh`, `sign_mac.sh` | Build, sign and notarize the Mac app |

## Run it

1. Open `MessangerApp.uproject` in Unreal Engine 5.8 (Mac).
2. Play in editor. The main widget is `Content/UI/Messaging/WBP_MessagingLayout`.

To build a standalone Mac app run `SourceArt/Messaging/package_mac.sh`. The script expects the engine at `/Volumes/Unreal/UE_5.8`, so change the path if yours is elsewhere.

`UMGAnimToolset` is prebuilt for Mac only. It is an editor-only plugin, so you need it only to rerun the generator scripts.
