import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import qs.Commons as Commons

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

  // Follow Setup > Language live. Missing Czech strings fall back to English.
  Commons.Translations {
    id: strings
    directory: Qt.resolvedUrl("i18n")
  }

  // The plugin's own checkout, so the actions work wherever it was installed.
  readonly property string pluginDir: String(Qt.resolvedUrl(".")).replace(/^file:\/\//, "").replace(/\/$/, "")

  // IDs, paths, commands, and catalog keys stay stable. Translation happens
  // only in the Text bindings below, so a language switch re-renders the UI.
  readonly property var actions: [
    {
      titleKey: "action.research.title",
      detailKey: "action.research.detail",
      command: ["bash", pluginDir + "/workspace/research-workspace.sh"]
    },
    {
      titleKey: "action.plan.title",
      detailKey: "action.plan.detail",
      command: ["omarchy-agent-prompt", "Read " + pluginDir + "/AGENTS.md and " + pluginDir
        + "/prompts/orchestrator-claude.md, then act as the orchestrator for this project."]
    },
    {
      titleKey: "action.audit.title",
      detailKey: "action.audit.detail",
      command: ["xdg-open", pluginDir + "/docs/no-extra-payment-audit.md"]
    },
    {
      titleKey: "action.notes.title",
      detailKey: "action.notes.detail",
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
          spacing: Commons.Style.space(12)
          LayoutMirroring.enabled: Commons.I18n.rightToLeft
          LayoutMirroring.childrenInherit: true

          Text {
            text: strings.t("panel.title")
            textFormat: Text.PlainText
            color: Qt.rgba(1, 1, 1, 0.55)
            font.family: Commons.Style.font.family
            font.pixelSize: Commons.Style.font.caption
            font.bold: true
            font.capitalization: Font.AllUppercase
            font.letterSpacing: 2
            Layout.alignment: Qt.AlignHCenter
          }

          Repeater {
            model: root.actions

            Rectangle {
              required property var modelData

              Layout.preferredWidth: Commons.Style.space(360)
              implicitHeight: label.implicitHeight + Commons.Style.space(24)
              radius: Commons.Style.cornerRadius
              color: area.containsMouse ? Qt.rgba(1, 1, 1, 0.16) : Qt.rgba(1, 1, 1, 0.08)

              ColumnLayout {
                id: label
                anchors.fill: parent
                anchors.margins: Commons.Style.space(12)
                spacing: Commons.Style.space(2)

                Text {
                  text: strings.t(modelData.titleKey)
                  textFormat: Text.PlainText
                  color: "white"
                  font.family: Commons.Style.font.family
                  font.pixelSize: Commons.Style.font.body
                  font.bold: true
                  wrapMode: Text.Wrap
                  Layout.fillWidth: true
                }

                Text {
                  text: strings.t(modelData.detailKey)
                  textFormat: Text.PlainText
                  color: Qt.rgba(1, 1, 1, 0.65)
                  font.family: Commons.Style.font.family
                  font.pixelSize: Commons.Style.font.bodySmall
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
