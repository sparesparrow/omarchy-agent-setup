import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import qs.Commons
import qs.Ui

// Agent setup: a small centered card with the setup's four entry points. Each
// button hands off to a command and closes the card, so nothing here runs
// agents or changes configuration by itself.
//
// Summon with: omarchy-shell shell summon sparesparrow.agent-setup '{}'
Item {
  id: root

  property var shell: null
  property var manifest: null

  property bool opened: false

  // The plugin's own checkout, so the actions work wherever it was installed.
  readonly property string pluginDir: String(Qt.resolvedUrl(".")).replace(/^file:\/\//, "").replace(/\/$/, "")

  readonly property var actions: [
    {
      title: "Research workspace",
      detail: "Open Perplexity and Gemini side by side on their own workspace",
      command: ["bash", pluginDir + "/workspace/research-workspace.sh"]
    },
    {
      title: "Plan with agents",
      detail: "Start your default agent as the orchestrator, following the contracts",
      command: ["omarchy-agent-prompt", "Read " + pluginDir + "/AGENTS.md and " + pluginDir
        + "/prompts/orchestrator-claude.md, then act as the orchestrator for this project."]
    },
    {
      title: "No-extra-payment audit",
      detail: "Check nothing can bill you before agents run",
      command: ["xdg-open", pluginDir + "/docs/no-extra-payment-audit.md"]
    },
    {
      title: "Research dispatcher notes",
      detail: "How research jobs become browser tasks for Codex",
      command: ["xdg-open", pluginDir + "/research/README.md"]
    }
  ]

  function open(payloadJson) {
    root.opened = true
    Qt.callLater(function() {
      if (root.opened) keyCatcher.forceActiveFocus()
    })
  }

  function close() {
    root.opened = false
  }

  function dismiss() {
    if (root.shell && typeof root.shell.hide === "function")
      root.shell.hide((root.manifest && root.manifest.id) || "sparesparrow.agent-setup")
    else close()
  }

  function run(command) {
    Quickshell.execDetached(command)
    dismiss()
  }

  OverlayWindow {
    shown: root.opened
    WlrLayershell.namespace: "agent-setup"

    Rectangle {
      anchors.fill: parent
      color: Qt.rgba(0, 0, 0, 0.78)

      MouseArea {
        anchors.fill: parent
        onClicked: root.dismiss()
      }
    }

    Item {
      id: keyCatcher
      anchors.fill: parent
      focus: true

      Keys.onEscapePressed: root.dismiss()

      Item {
        anchors.centerIn: parent
        width: content.implicitWidth
        height: content.implicitHeight

        // Swallow clicks so only the scrim outside the card dismisses.
        MouseArea { anchors.fill: parent; onClicked: {} }

        ColumnLayout {
          id: content
          anchors.fill: parent
          spacing: Style.space(12)

          Text {
            text: "AGENT SETUP"
            color: Qt.rgba(1, 1, 1, 0.55)
            font.family: Style.font.family
            font.pixelSize: Style.font.caption
            font.bold: true
            font.letterSpacing: 2
            Layout.alignment: Qt.AlignHCenter
          }

          Repeater {
            model: root.actions

            Rectangle {
              required property var modelData

              Layout.preferredWidth: Style.space(360)
              implicitHeight: label.implicitHeight + Style.space(24)
              radius: Style.cornerRadius
              color: area.containsMouse ? Qt.rgba(1, 1, 1, 0.16) : Qt.rgba(1, 1, 1, 0.08)

              ColumnLayout {
                id: label
                anchors.fill: parent
                anchors.margins: Style.space(12)
                spacing: Style.space(2)

                Text {
                  text: modelData.title
                  color: "white"
                  font.family: Style.font.family
                  font.pixelSize: Style.font.body
                  font.bold: true
                }

                Text {
                  text: modelData.detail
                  color: Qt.rgba(1, 1, 1, 0.65)
                  font.family: Style.font.family
                  font.pixelSize: Style.font.bodySmall
                  wrapMode: Text.Wrap
                  Layout.fillWidth: true
                }
              }

              MouseArea {
                id: area
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.run(modelData.command)
              }
            }
          }
        }
      }
    }
  }
}
