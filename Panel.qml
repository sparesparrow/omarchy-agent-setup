import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import qs.Commons as Commons

// Agent setup entry points. Each button opens a reviewed local command and
// closes the card. Setup scripts ask again before installing or writing config.
//
// Summon with: omarchy-shell shell summon sparesparrow.agent-setup '{}'
Item {
  id: root

  property var shell: null
  property var manifest: null
  property bool opened: false

  Commons.Translations {
    id: strings
    directory: Qt.resolvedUrl("i18n")
  }

  readonly property string pluginDir: String(Qt.resolvedUrl(".")).replace(/^file:\/\//, "").replace(/\/$/, "")

  readonly property var actions: [
    {
      titleKey: "action.research.title",
      detailKey: "action.research.detail",
      command: ["bash", pluginDir + "/workspace/research-workspace.sh"]
    },
    {
      titleKey: "action.openclaw.title",
      detailKey: "action.openclaw.detail",
      command: ["bash", pluginDir + "/setup/openclaw-cs.sh"]
    },
    {
      titleKey: "action.voxtype.title",
      detailKey: "action.voxtype.detail",
      command: ["bash", pluginDir + "/setup/voxtype.sh"]
    },
    {
      titleKey: "action.plugins.title",
      detailKey: "action.plugins.detail",
      command: ["bash", pluginDir + "/setup/plugins.sh"]
    },
    {
      titleKey: "action.omp.title",
      detailKey: "action.omp.detail",
      command: ["bash", pluginDir + "/setup/omp-presets.sh"]
    },
    {
      titleKey: "action.mia.title",
      detailKey: "action.mia.detail",
      command: ["bash", pluginDir + "/setup/mia-voice.sh"]
    },
    {
      titleKey: "action.catalog.title",
      detailKey: "action.catalog.detail",
      command: ["xdg-open", pluginDir + "/prompt-catalog/README.md"]
    },
    {
      titleKey: "action.mcp.title",
      detailKey: "action.mcp.detail",
      command: ["bash", pluginDir + "/setup/mcp-skills.sh"]
    },
    {
      titleKey: "action.team.title",
      detailKey: "action.team.detail",
      command: ["bash", pluginDir + "/setup/agent-team.sh"]
    },
    {
      titleKey: "action.repositories.title",
      detailKey: "action.repositories.detail",
      command: ["bash", pluginDir + "/setup/github-repositories.sh"]
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
