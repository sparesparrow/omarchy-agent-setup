import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
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
  property string language: "en"
  property int focusIndex: 0
  property var englishStrings: ({})
  property var czechStrings: ({})

  function t(key) {
    var selected = language === "cs" ? czechStrings : englishStrings
    return selected[key] || englishStrings[key] || key
  }

  // Omarchy's current qs.Commons module has no translation service. Load the
  // plugin-owned catalogs and keep the selector live while the panel is open.
  FileView {
    path: Qt.resolvedUrl("i18n/en.json")
    watchChanges: false
    printErrors: false
    onLoaded: {
      try { root.englishStrings = JSON.parse(text()) }
      catch (error) { console.warn("agent-setup: cannot load English catalog", error) }
    }
  }

  FileView {
    path: Qt.resolvedUrl("i18n/cs.json")
    watchChanges: false
    printErrors: false
    onLoaded: {
      try { root.czechStrings = JSON.parse(text()) }
      catch (error) { console.warn("agent-setup: cannot load Czech catalog", error) }
    }
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
      titleKey: "action.ecosystem.title",
      detailKey: "action.ecosystem.detail",
      command: ["bash", pluginDir + "/setup/omarchy-ecosystem.sh"]
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
    root.focusIndex = 0
    Qt.callLater(function() {
      if (root.opened) keyCatcher.forceActiveFocus()
    })
  }

  function moveFocus(delta) {
    var count = root.actions.length + 2
    root.focusIndex = (root.focusIndex + delta + count) % count
  }

  function activateFocused() {
    if (root.focusIndex === 0) root.language = "en"
    else if (root.focusIndex === 1) root.language = "cs"
    else root.run(root.actions[root.focusIndex - 2].command)
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

  PanelWindow {
    visible: root.opened
    anchors { top: true; bottom: true; left: true; right: true }
    color: "transparent"
    WlrLayershell.namespace: "agent-setup"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: root.opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    exclusionMode: ExclusionMode.Ignore

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

      Keys.onPressed: function(event) {
        if (event.key === Qt.Key_Escape) {
          root.dismiss()
          event.accepted = true
        } else if (event.key === Qt.Key_Tab || event.key === Qt.Key_Down) {
          root.moveFocus(1)
          event.accepted = true
        } else if (event.key === Qt.Key_Backtab || event.key === Qt.Key_Up) {
          root.moveFocus(-1)
          event.accepted = true
        } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter || event.key === Qt.Key_Space) {
          root.activateFocused()
          event.accepted = true
        }
      }

      Item {
        anchors.centerIn: parent
        width: content.implicitWidth
        height: content.implicitHeight

        Rectangle {
          anchors.fill: parent
          color: Qt.rgba(0.07, 0.07, 0.07, 0.98)
          radius: Commons.Style.cornerRadius
        }

        // Swallow clicks so only the scrim outside the card dismisses.
        MouseArea { anchors.fill: parent; onClicked: {} }

        ColumnLayout {
          id: content
          anchors.fill: parent
          spacing: Commons.Style.space(12)
          LayoutMirroring.enabled: false

          Text {
            text: root.t("panel.title")
            textFormat: Text.PlainText
            color: Qt.rgba(1, 1, 1, 0.55)
            font.family: Commons.Style.font.family
            font.pixelSize: Commons.Style.font.caption
            font.bold: true
            font.capitalization: Font.AllUppercase
            font.letterSpacing: 2
            Layout.alignment: Qt.AlignHCenter
          }

          RowLayout {
            spacing: Commons.Style.space(12)
            Layout.alignment: Qt.AlignHCenter

            Text {
              text: "EN"
              textFormat: Text.PlainText
              color: root.language === "en" ? "white" : Qt.rgba(1, 1, 1, 0.55)
              font.family: Commons.Style.font.family
              font.pixelSize: Commons.Style.font.bodySmall
              font.bold: root.focusIndex === 0
              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: { root.focusIndex = 0; root.language = "en" }
              }
            }

            Text {
              text: "Čeština"
              textFormat: Text.PlainText
              color: root.language === "cs" ? "white" : Qt.rgba(1, 1, 1, 0.55)
              font.family: Commons.Style.font.family
              font.pixelSize: Commons.Style.font.bodySmall
              font.bold: root.focusIndex === 1
              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: { root.focusIndex = 1; root.language = "cs" }
              }
            }
          }

          Repeater {
            model: root.actions
            Rectangle {
              required property var modelData
              required property int index

              Layout.preferredWidth: Commons.Style.space(360)
              implicitHeight: label.implicitHeight + Commons.Style.space(24)
              radius: Commons.Style.cornerRadius
              color: area.containsMouse || root.focusIndex === index + 2
                ? Qt.rgba(1, 1, 1, 0.16) : Qt.rgba(1, 1, 1, 0.08)

              ColumnLayout {
                id: label
                anchors.fill: parent
                anchors.margins: Commons.Style.space(12)
                spacing: Commons.Style.space(2)

                Text {
                  text: root.t(modelData.titleKey)
                  textFormat: Text.PlainText
                  color: "white"
                  font.family: Commons.Style.font.family
                  font.pixelSize: Commons.Style.font.body
                  font.bold: true
                  wrapMode: Text.Wrap
                  Layout.fillWidth: true
                }

                Text {
                  text: root.t(modelData.detailKey)
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
                onClicked: { root.focusIndex = index + 2; root.run(modelData.command) }
              }
            }
          }
        }
      }
    }
  }
}
