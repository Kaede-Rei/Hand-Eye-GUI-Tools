import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 1480
    height: 920
    minimumWidth: 1180
    minimumHeight: 760
    visible: true
    color: "transparent"
    title: "多功能手眼标定工具"
    flags: Qt.FramelessWindowHint | Qt.Window

    readonly property color macBlue: "#007AFF"
    readonly property color macBluePressed: "#0057B8"
    readonly property color macBlueHover: "#0A84FF"
    readonly property color macBlueSoft: "#EAF4FF"
    readonly property color macBluePressedSoft: "#D6EAFF"
    readonly property color bg0: "#ECECF0"
    readonly property color sidebarBg: "#F5F5F7"
    readonly property color contentBg: "#FFFFFF"
    readonly property color panelBg: "#FFFFFF"
    readonly property color fieldBg: "#F5F5F7"
    readonly property color textPrimary: "#1D1D1F"
    readonly property color textSecondary: "#6E6E73"
    readonly property string fontStack: "San Francisco, SF Pro Text, PingFang SC, Helvetica Neue, Arial, sans-serif"

    property var state: ({})
    property var tasks: []
    property var taskNames: []
    property var navItems: ["项目", "相机", "标定板", "机器人 / TF", "任务", "采样", "标定 / 报告"]
    property int currentPage: 0
    property string activeTask: ""
    property string previewCamera: "wrist"
    property string previewSource: "image://camera/preview?rev=0"
    property string previewStatus: "等待相机画面"
    property string tfText: "未查询"
    property string resultText: ""
    property string logs: ""
    property var cameraFields: ({})
    property bool isBooting: true
    property real pagePopScale: 1.0
    property real pagePopOffset: 0
    readonly property bool maximized: root.visibility === Window.Maximized
    readonly property int frameMargin: maximized ? 0 : 18
    readonly property int frameRadius: maximized ? 0 : 12

    Component.onCompleted: {
        startupTimer.start()
    }

    Timer {
        id: startupTimer
        interval: 70
        repeat: false
        onTriggered: {
            startupProgress.indeterminate = false
            startupProgress.value = 0.58
            loadTimer.start()
        }
    }

    Timer {
        id: loadTimer
        interval: 90
        repeat: false
        onTriggered: {
            startupProgress.value = 0.86
            loadState(JSON.parse(backend.initialState()))
            appendLog("Qt GUI 已启动")
            startupDoneTimer.start()
        }
    }

    Timer {
        id: startupDoneTimer
        interval: 220
        repeat: false
        onTriggered: {
            startupProgress.value = 1.0
            root.isBooting = false
        }
    }

    /*
     * 启动阶段先让窗口和加载遮罩完成首帧绘制，再读取配置。
     * 这样 ROS / Python 环境较慢时不会出现长时间空白窗口。
     */

    Connections {
        target: backend
        function onLogChanged(message) { appendLog(message) }
        function onStateChanged(rawState) { loadState(JSON.parse(rawState)) }
        function onImageChanged(url) {
            previewSource = ""
            previewSource = url
        }
        function onPreviewStatusChanged(message) { previewStatus = message }
    }

    function loadState(nextState) {
        state = nextState
        tasks = nextState.tasks || []
        taskNames = tasks.map(function(t) { return t.name })
        activeTask = taskNames.length > 0 ? taskNames[0] : ""
        projectName.text = nextState.projectName || ""
        datasetRoot.text = nextState.datasetRoot || ""
        outputRoot.text = nextState.outputRoot || ""
        configPath.text = nextState.configPath || ""
        baseFrame.text = nextState.baseFrame || "base_link"
        toolFrame.text = nextState.toolFrame || "link_tcp"
        tfTimeout.text = nextState.tfTimeout || "0.3"
        boardType.currentIndex = nextState.boardType === "chessboard" ? 1 : 0
        chessCols.value = nextState.chessCols || 9
        chessRows.value = nextState.chessRows || 6
        squareSize.text = nextState.squareSize || "0.030"
        charucoX.value = nextState.charucoX || 8
        charucoY.value = nextState.charucoY || 11
        markerLength.text = nextState.markerLength || "0.022"
        dictionary.text = nextState.dictionary || "DICT_5X5_100"
        fx.text = nextState.fx || "600"
        fy.text = nextState.fy || "600"
        cx.text = nextState.cx || "320"
        cy.text = nextState.cy || "240"
        dist.text = nextState.dist || "0,0,0,0,0"
        sampleId.value = nextState.sampleId || 1
        loadCameraFields("wrist", nextState.cameras.wrist || {})
        loadCameraFields("mid", nextState.cameras.mid || {})
        loadCameraFields("far", nextState.cameras.far || {})
    }

    function loadCameraFields(name, cfg) {
        var card = cameraFields[name]
        if (!card)
            return
        card.imageTopic.text = cfg.imageTopic || ""
        card.cameraInfoTopic.text = cfg.cameraInfoTopic || ""
        card.frameId.text = cfg.frameId || ""
        card.role.text = cfg.role || ""
        card.status.text = cfg.status || "未连接"
    }

    function collectState() {
        return {
            configPath: configPath.text,
            projectName: projectName.text,
            datasetRoot: datasetRoot.text,
            outputRoot: outputRoot.text,
            baseFrame: baseFrame.text,
            toolFrame: toolFrame.text,
            tfTimeout: tfTimeout.text,
            boardType: boardType.currentText,
            chessCols: chessCols.value,
            chessRows: chessRows.value,
            squareSize: squareSize.text,
            charucoX: charucoX.value,
            charucoY: charucoY.value,
            markerLength: markerLength.text,
            dictionary: dictionary.text,
            fx: fx.text,
            fy: fy.text,
            cx: cx.text,
            cy: cy.text,
            dist: dist.text,
            sampleId: sampleId.value,
            minId: minId.value,
            maxId: maxId.value,
            method: methodBox.currentText,
            tToolBoard: tToolBoard.text,
            activeTask: activeTask,
            previewCamera: previewCamera,
            cameras: {
                wrist: cameraPayload("wrist"),
                mid: cameraPayload("mid"),
                far: cameraPayload("far")
            }
        }
    }

    function cameraPayload(name) {
        var card = cameraFields[name]
        return {
            imageTopic: card.imageTopic.text,
            cameraInfoTopic: card.cameraInfoTopic.text,
            frameId: card.frameId.text,
            role: card.role.text
        }
    }

    function stateJson() { return JSON.stringify(collectState()) }

    function appendLog(message) {
        var now = new Date()
        logs += "[" + now.toLocaleTimeString() + "] " + message + "\n"
        logArea.text = logs
        logArea.cursorPosition = logArea.length
    }

    function activeTaskHint() {
        for (var i = 0; i < tasks.length; ++i) {
            if (tasks[i].name === activeTask) {
                if (tasks[i].type === "camera_to_camera")
                    return "需要 " + tasks[i].reference_camera + " 与 " + tasks[i].target_camera + " 同时看到同一块标定板。"
                return "需要 " + tasks[i].camera + " 图像、camera_info、" + baseFrame.text + " -> " + toolFrame.text + " TF。"
            }
        }
        return "请选择任务。"
    }

    function toggleMaximize() {
        if (root.visibility === Window.Maximized)
            root.showNormal()
        else
            root.showMaximized()
    }

    background: Rectangle {
        anchors.fill: parent
        color: "transparent"
    }

    component WindowShadow: Item {
        anchors.fill: parent
        visible: !root.maximized
        opacity: root.maximized ? 0 : 1
        Behavior on opacity { NumberAnimation { duration: 160 } }
        Rectangle {
            anchors.fill: parent
            anchors.margins: 18
            radius: 18
            color: "#000000"
            opacity: 0.11
        }
        Rectangle {
            anchors.fill: parent
            anchors.margins: 10
            radius: 18
            color: "#000000"
            opacity: 0.06
        }
    }

    component AppText: Text {
        color: root.textPrimary
        font.family: root.fontStack
        font.pixelSize: 14
        renderType: Text.NativeRendering
    }

    component FieldLabel: AppText {
        color: root.textSecondary
        font.pixelSize: 13
        font.weight: Font.DemiBold
        Layout.alignment: Qt.AlignVCenter
    }

    component SectionNote: Rectangle {
        property alias text: noteText.text
        Layout.fillWidth: true
        radius: 12
        color: "#F5F5F7"
        border.color: "#E5E5EA"
        implicitHeight: noteText.implicitHeight + 24
        AppText {
            id: noteText
            anchors.fill: parent
            anchors.margins: 12
            color: "#515154"
            wrapMode: Text.WordWrap
            font.pixelSize: 13
            lineHeight: 1.18
        }
    }

    component Card: Rectangle {
        color: root.panelBg
        border.color: "#E5E5EA"
        border.width: 1
        radius: 14
    }

    component ModernField: TextField {
        selectByMouse: true
        color: root.textPrimary
        placeholderTextColor: "#7A7A80"
        selectedTextColor: "white"
        selectionColor: root.macBlue
        font.family: root.fontStack
        font.pixelSize: 14
        leftPadding: 12
        rightPadding: 12
        background: Rectangle {
            radius: 9
            color: parent.activeFocus ? "#FFFFFF" : root.fieldBg
            border.color: parent.activeFocus ? root.macBlue : "#D2D2D7"
            border.width: parent.activeFocus ? 2 : 1
            Rectangle {
                anchors.fill: parent
                anchors.margins: -3
                radius: 12
                color: "transparent"
                border.color: root.macBlue
                border.width: parent.parent.activeFocus ? 1 : 0
                opacity: parent.parent.activeFocus ? 0.38 : 0
                Behavior on opacity { NumberAnimation { duration: 120 } }
            }
        }
    }

    component MacComboBox: ComboBox {
        id: combo
        font.family: root.fontStack
        font.pixelSize: 14
        contentItem: AppText {
            text: parent.displayText
            color: root.textPrimary
            verticalAlignment: Text.AlignVCenter
            leftPadding: 12
            rightPadding: 34
        }
        background: Rectangle {
            radius: 9
            color: combo.down ? root.macBluePressedSoft : combo.hovered ? root.macBlueSoft : root.fieldBg
            border.color: parent.activeFocus ? root.macBlue : "#D2D2D7"
            border.width: parent.activeFocus ? 2 : 1
            Behavior on color { ColorAnimation { duration: 140; easing.type: Easing.OutCubic } }
            Behavior on border.color { ColorAnimation { duration: 120 } }
        }
        indicator: AppText {
            x: combo.width - width - 13
            y: combo.topPadding + (combo.availableHeight - height) / 2
            text: "⌄"
            color: combo.down || combo.activeFocus ? root.macBlue : root.textSecondary
            font.pixelSize: 16
            rotation: combo.popup.visible ? 180 : 0
            Behavior on rotation { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
            Behavior on color { ColorAnimation { duration: 120 } }
        }
        delegate: ItemDelegate {
            id: comboItem
            width: parent.width
            required property int index
            required property string modelData
            contentItem: AppText {
                text: comboItem.modelData
                color: combo.currentIndex === comboItem.index ? "white" : root.textPrimary
                font.weight: combo.currentIndex === comboItem.index ? Font.DemiBold : Font.Normal
            }
            background: Rectangle {
                radius: 7
                color: combo.currentIndex === comboItem.index ? root.macBlue : comboItem.hovered ? root.macBlueSoft : "#FFFFFF"
                Behavior on color { ColorAnimation { duration: 120; easing.type: Easing.OutCubic } }
            }
        }
        popup: Popup {
            y: combo.height + 6
            width: combo.width
            implicitHeight: Math.min(contentItem.implicitHeight + 12, 260)
            padding: 6
            transformOrigin: Item.Top
            enter: Transition {
                ParallelAnimation {
                    NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 130; easing.type: Easing.OutCubic }
                    NumberAnimation { property: "scale"; from: 0.96; to: 1; duration: 150; easing.type: Easing.OutCubic }
                }
            }
            exit: Transition {
                ParallelAnimation {
                    NumberAnimation { property: "opacity"; to: 0; duration: 90; easing.type: Easing.InCubic }
                    NumberAnimation { property: "scale"; to: 0.98; duration: 90; easing.type: Easing.InCubic }
                }
            }
            contentItem: ListView {
                clip: true
                implicitHeight: contentHeight
                model: combo.popup.visible ? combo.delegateModel : null
                currentIndex: combo.highlightedIndex
            }
            background: Rectangle {
                radius: 12
                color: "#FFFFFF"
                border.color: "#D2D2D7"
                border.width: 1
            }
        }
    }

    component MacSpinBox: SpinBox {
        font.family: root.fontStack
        font.pixelSize: 14
        editable: true
        contentItem: TextInput {
            text: parent.textFromValue(parent.value, parent.locale)
            color: root.textPrimary
            selectionColor: root.macBlue
            selectedTextColor: "white"
            horizontalAlignment: Qt.AlignHCenter
            verticalAlignment: Qt.AlignVCenter
            font: parent.font
            readOnly: !parent.editable
            validator: parent.validator
            inputMethodHints: Qt.ImhFormattedNumbersOnly
        }
        background: Rectangle {
            radius: 9
            color: root.fieldBg
            border.color: parent.activeFocus ? root.macBlue : "#D2D2D7"
            border.width: parent.activeFocus ? 2 : 1
        }
    }

    component PrimaryButton: Button {
        id: btn
        font.family: root.fontStack
        font.pixelSize: 14
        font.weight: Font.DemiBold
        contentItem: AppText {
            text: btn.text
            color: "white"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            font: btn.font
        }
        background: Rectangle {
            radius: 10
            color: btn.down ? root.macBluePressed : btn.hovered ? root.macBlueHover : root.macBlue
            Behavior on color { ColorAnimation { duration: 120; easing.type: Easing.OutCubic } }
        }
    }

    component SecondaryButton: Button {
        id: btn
        font.family: root.fontStack
        font.pixelSize: 14
        font.weight: Font.DemiBold
        contentItem: AppText {
            text: btn.text
            color: root.textPrimary
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            font: btn.font
        }
        background: Rectangle {
            radius: 10
            color: btn.down ? root.macBluePressedSoft : btn.hovered ? root.macBlueSoft : "#F2F2F7"
            border.color: "#D2D2D7"
            Behavior on color { ColorAnimation { duration: 130; easing.type: Easing.OutCubic } }
        }
    }

    component TrafficLight: Rectangle {
        id: light
        property string symbol: ""
        property color baseColor: "#FF5F57"
        signal clicked()
        width: 13
        height: 13
        radius: 7
        color: baseColor
        border.color: Qt.rgba(0, 0, 0, 0.18)
        AppText {
            anchors.centerIn: parent
            text: light.symbol
            color: Qt.rgba(0, 0, 0, 0.62)
            font.pixelSize: 9
            font.weight: Font.Bold
            opacity: lightMouse.containsMouse ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: 100 } }
        }
        MouseArea {
            id: lightMouse
            anchors.fill: parent
            hoverEnabled: true
            onClicked: light.clicked()
        }
    }

    component NavButton: Rectangle {
        id: nav
        property string label: ""
        property int index: 0
        readonly property bool selected: root.currentPage === index
        width: parent ? parent.width : 220
        height: 38
        radius: 9
        color: selected ? root.macBlue : navMouse.pressed ? "#CBE4FF" : navMouse.containsMouse ? "#E2F1FF" : "transparent"
        scale: navMouse.pressed && !selected ? 0.985 : 1
        Behavior on color { ColorAnimation { duration: 160; easing.type: Easing.OutCubic } }
        Behavior on scale { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
        Rectangle {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            width: nav.selected ? 4 : 0
            height: 20
            radius: 2
            color: "#FFFFFF"
            opacity: nav.selected ? 1 : 0
            Behavior on width { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }
            Behavior on opacity { NumberAnimation { duration: 140 } }
        }
        AppText {
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: 14
            text: nav.label
            color: nav.selected ? "white" : "#1D1D1F"
            font.pixelSize: 14
            font.weight: nav.selected ? Font.DemiBold : Font.Normal
            Behavior on color { ColorAnimation { duration: 140 } }
        }
        MouseArea {
            id: navMouse
            anchors.fill: parent
            hoverEnabled: true
            onClicked: root.currentPage = nav.index
        }
    }

    component MacScrollView: ScrollView {
        id: scroller
        property int edgeDirection: 1
        property real edgeOffset: 0
        property double lastEdgePulseAt: 0
        contentWidth: availableWidth
        clip: true
        ScrollBar.vertical.policy: ScrollBar.AsNeeded
        transform: Translate { y: scroller.edgeOffset }
        Behavior on edgeOffset { NumberAnimation { duration: 80; easing.type: Easing.OutCubic } }

        function pulseEdge(deltaY) {
            var flickable = contentItem
            var maxY = Math.max(0, flickable.contentHeight - flickable.height)
            if (maxY <= 1)
                return
            var atTop = flickable.contentY <= 0.5
            var atBottom = flickable.contentY >= maxY - 0.5
            var now = Date.now()
            if (((deltaY > 0 && atTop) || (deltaY < 0 && atBottom)) && now - lastEdgePulseAt > 260) {
                lastEdgePulseAt = now
                edgeDirection = deltaY > 0 ? 1 : -1
                edgePulse.restart()
            }
        }

        WheelHandler {
            target: null
            blocking: false
            onWheel: function(wheel) {
                scroller.pulseEdge(wheel.angleDelta.y)
            }
        }

        SequentialAnimation {
            id: edgePulse
            NumberAnimation { target: scroller; property: "edgeOffset"; to: scroller.edgeDirection * 7; duration: 70; easing.type: Easing.OutCubic }
            NumberAnimation { target: scroller; property: "edgeOffset"; to: 0; duration: 210; easing.type: Easing.OutElastic }
        }
    }

    component CameraCard: Card {
        property string cameraName: "wrist"
        property alias imageTopic: imageTopicField
        property alias cameraInfoTopic: infoTopicField
        property alias frameId: frameIdField
        property alias role: roleField
        property alias status: statusLabel
        Layout.fillWidth: true
        implicitHeight: 236
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 9
            RowLayout {
                Layout.fillWidth: true
                AppText {
                    text: cameraName
                    font.pixelSize: 17
                    font.weight: Font.Bold
                    Layout.fillWidth: true
                }
                AppText {
                    id: statusLabel
                    text: "未连接"
                color: "#248A3D"
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                }
            }
            GridLayout {
                columns: 2
                rowSpacing: 8
                columnSpacing: 10
                Layout.fillWidth: true
                FieldLabel { text: "图像话题" }
                ModernField { id: imageTopicField; Layout.fillWidth: true }
                FieldLabel { text: "内参话题" }
                ModernField { id: infoTopicField; Layout.fillWidth: true }
                FieldLabel { text: "frame_id" }
                ModernField { id: frameIdField; Layout.fillWidth: true }
                FieldLabel { text: "role" }
                ModernField { id: roleField; Layout.fillWidth: true }
            }
        }
    }

    WindowShadow { anchors.fill: parent }

    Rectangle {
        id: appFrame
        anchors.fill: parent
        anchors.margins: root.frameMargin
        radius: root.frameRadius
        color: root.contentBg
        border.color: "#D2D2D7"
        clip: true
        Behavior on radius { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }

        Rectangle {
            anchors.fill: parent
            color: "transparent"
            opacity: 0
        }

        Rectangle {
            id: titleBar
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: 52
            color: "#F5F5F7"
            border.color: "#D2D2D7"

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.LeftButton
                onPressed: root.startSystemMove()
                onDoubleClicked: root.toggleMaximize()
            }

            Row {
                anchors.left: parent.left
                anchors.leftMargin: 18
                anchors.verticalCenter: parent.verticalCenter
                spacing: 8
                TrafficLight { baseColor: "#FF5F57"; symbol: "×"; onClicked: root.close() }
                TrafficLight { baseColor: "#FFBD2E"; symbol: "-"; onClicked: root.showMinimized() }
                TrafficLight { baseColor: "#28C840"; symbol: "+"; onClicked: root.toggleMaximize() }
            }

            AppText {
                anchors.centerIn: parent
                text: "多功能手眼标定工具"
                color: "#3A3A3C"
                font.pixelSize: 13
                font.weight: Font.DemiBold
            }
        }

        RowLayout {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: titleBar.bottom
            anchors.bottom: parent.bottom
            spacing: 0

            Rectangle {
                id: sidebar
                Layout.preferredWidth: 258
                Layout.fillHeight: true
                color: root.sidebarBg
                border.color: "#D2D2D7"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 18
                    spacing: 14
                    AppText {
                        text: "Calibration"
                        font.pixelSize: 25
                        font.weight: Font.Bold
                        color: root.textPrimary
                    }
                    AppText {
                        text: "eye-in-hand · eye-to-hand · camera-to-camera"
                        color: root.textSecondary
                        font.pixelSize: 12
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: "#D2D2D7"
                    }

                    Column {
                        Layout.fillWidth: true
                        spacing: 5
                        Repeater {
                            model: root.navItems
                            NavButton {
                                label: modelData
                                index: model.index
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }

                    Card {
                        Layout.fillWidth: true
                        implicitHeight: 120
                        color: "#FFFFFF"
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 8
                            AppText {
                                text: "预览相机"
                                color: root.textSecondary
                                font.pixelSize: 12
                                font.weight: Font.DemiBold
                            }
                            MacComboBox {
                                id: previewCameraBox
                                model: ["wrist", "mid", "far"]
                                Layout.fillWidth: true
                                onCurrentTextChanged: {
                                    root.previewCamera = currentText
                                    backend.setPreviewCamera(currentText)
                                }
                            }
                            AppText {
                                text: root.previewStatus
                                color: "#248A3D"
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                        }
                    }
                }
            }

            Rectangle {
                id: content
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: root.contentBg

                SplitView {
                    anchors.fill: parent
                    anchors.margins: 22
                    orientation: Qt.Vertical

                    handle: Rectangle {
                        implicitHeight: 10
                        color: SplitHandle.hovered || SplitHandle.pressed ? "#E2F1FF" : "transparent"
                        Rectangle {
                            anchors.centerIn: parent
                            width: 64
                            height: 3
                            radius: 2
                            color: SplitHandle.pressed ? root.macBlue : SplitHandle.hovered ? "#8DC6FF" : "#D2D2D7"
                            Behavior on color { ColorAnimation { duration: 120 } }
                        }
                        Behavior on color { ColorAnimation { duration: 120 } }
                    }

                    SplitView {
                        SplitView.fillWidth: true
                        SplitView.minimumHeight: 250
                        SplitView.preferredHeight: 470
                        orientation: Qt.Horizontal

                        handle: Rectangle {
                            implicitWidth: 10
                            color: SplitHandle.hovered || SplitHandle.pressed ? root.macBlueSoft : "transparent"
                            Rectangle {
                                anchors.centerIn: parent
                                width: 3
                                height: 54
                                radius: 2
                                color: SplitHandle.pressed ? root.macBlue : SplitHandle.hovered ? "#9CCBFF" : "#D2D2D7"
                                Behavior on color { ColorAnimation { duration: 120 } }
                            }
                            Behavior on color { ColorAnimation { duration: 120 } }
                        }

                        Card {
                            SplitView.fillWidth: true
                            SplitView.minimumWidth: 520
                            SplitView.preferredWidth: 860
                            clip: true
                            color: "#111113"
                            Image {
                                anchors.fill: parent
                                anchors.margins: 1
                                source: root.previewSource
                                fillMode: Image.PreserveAspectFit
                                cache: false
                                asynchronous: true
                                opacity: status === Image.Ready ? 1 : 0.45
                                Behavior on opacity { NumberAnimation { duration: 160 } }
                            }
                            Rectangle {
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.bottom: parent.bottom
                                height: 48
                                color: Qt.rgba(0, 0, 0, 0.46)
                                AppText {
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.left: parent.left
                                    anchors.leftMargin: 16
                                    text: root.previewStatus
                                    color: "#FFFFFF"
                                    font.pixelSize: 13
                                    font.weight: Font.DemiBold
                                }
                            }
                        }

                        Card {
                            SplitView.minimumWidth: 300
                            SplitView.preferredWidth: 330
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 16
                                spacing: 10
                                AppText {
                                    text: "快捷操作"
                                    font.pixelSize: 18
                                    font.weight: Font.Bold
                                }
                                SecondaryButton {
                                    text: "连接 ROS 话题"
                                    Layout.fillWidth: true
                                    onClicked: backend.connectRos(root.stateJson())
                                }
                                SecondaryButton {
                                    text: "测试当前检测"
                                    Layout.fillWidth: true
                                    onClicked: backend.testDetection(root.stateJson())
                                }
                                PrimaryButton {
                                    text: "采集当前任务样本"
                                    Layout.fillWidth: true
                                    onClicked: sampleId.value = backend.captureSample(root.stateJson())
                                }
                                AppText {
                                    text: "当前页：" + root.navItems[root.currentPage]
                                    color: root.textSecondary
                                    font.pixelSize: 12
                                }
                            }
                        }
                    }

                    Item {
                        SplitView.fillWidth: true
                        SplitView.fillHeight: true
                        SplitView.minimumHeight: 250

                        ColumnLayout {
                            anchors.fill: parent
                            spacing: 18

                            Card {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                color: "#FFFFFF"
                                clip: true

                                StackLayout {
                                    id: stack
                                    anchors.fill: parent
                                    anchors.margins: 18
                                    currentIndex: root.currentPage
                                    scale: root.pagePopScale
                                    transformOrigin: Item.Center
                                    transform: Translate { y: root.pagePopOffset }
                                    onCurrentIndexChanged: {
                                        opacity = 0
                                        root.pagePopScale = 0.965
                                        root.pagePopOffset = 18
                                        pagePop.restart()
                                    }
                                    ParallelAnimation {
                                        id: pagePop
                                        NumberAnimation { target: stack; property: "opacity"; to: 1; duration: 180; easing.type: Easing.OutCubic }
                                        NumberAnimation { target: root; property: "pagePopScale"; to: 1; duration: 240; easing.type: Easing.OutBack }
                                        NumberAnimation { target: root; property: "pagePopOffset"; to: 0; duration: 230; easing.type: Easing.OutCubic }
                                    }

                            MacScrollView {
                                contentWidth: availableWidth
                                ColumnLayout {
                                    width: parent.width
                                    spacing: 16
                                    SectionNote { text: "项目页用于管理本次标定的配置文件、数据集目录和结果输出目录。建议每次正式标定使用独立 dataset_root。" }
                                    GridLayout {
                                        columns: 2
                                        rowSpacing: 12
                                        columnSpacing: 14
                                        Layout.fillWidth: true
                                        FieldLabel { text: "项目名称" }
                                        ModernField { id: projectName; Layout.fillWidth: true }
                                        FieldLabel { text: "数据集目录" }
                                        ModernField { id: datasetRoot; Layout.fillWidth: true }
                                        FieldLabel { text: "输出目录" }
                                        ModernField { id: outputRoot; Layout.fillWidth: true }
                                        FieldLabel { text: "配置文件" }
                                        ModernField { id: configPath; Layout.fillWidth: true }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        PrimaryButton { text: "保存配置"; Layout.fillWidth: true; onClicked: backend.saveConfig(root.stateJson()) }
                                        SecondaryButton { text: "加载配置"; Layout.fillWidth: true; onClicked: backend.loadConfig(configPath.text) }
                                    }
                                }
                            }

                            MacScrollView {
                                contentWidth: availableWidth
                                ColumnLayout {
                                    width: parent.width
                                    spacing: 14
                                    SectionNote { text: "相机页配置多路 ROS 图像话题。采样时按任务自动保存需要的相机帧，frame_id 应填写对应 optical frame。" }
                                    CameraCard { id: wristCard; cameraName: "wrist"; Component.onCompleted: cameraFields.wrist = wristCard }
                                    CameraCard { id: midCard; cameraName: "mid"; Component.onCompleted: cameraFields.mid = midCard }
                                    CameraCard { id: farCard; cameraName: "far"; Component.onCompleted: cameraFields.far = farCard }
                                }
                            }

                            MacScrollView {
                                contentWidth: availableWidth
                                ColumnLayout {
                                    width: parent.width
                                    spacing: 16
                                    SectionNote { text: "标定板页设置检测参数和相机内参。连接 ROS 后若 camera_info 可用，检测会优先使用话题内参；这里是备用内参。" }
                                    GridLayout {
                                        columns: 2
                                        rowSpacing: 12
                                        columnSpacing: 14
                                        Layout.fillWidth: true
                                        FieldLabel { text: "标定板类型" }
                                        MacComboBox { id: boardType; model: ["charuco", "chessboard"]; Layout.fillWidth: true }
                                        FieldLabel { text: "棋盘格内角点列数" }
                                        MacSpinBox { id: chessCols; from: 2; to: 30; Layout.fillWidth: true }
                                        FieldLabel { text: "棋盘格内角点行数" }
                                        MacSpinBox { id: chessRows; from: 2; to: 30; Layout.fillWidth: true }
                                        FieldLabel { text: "方格边长 m" }
                                        ModernField { id: squareSize; Layout.fillWidth: true }
                                        FieldLabel { text: "ChArUco 横向方格数" }
                                        MacSpinBox { id: charucoX; from: 2; to: 30; Layout.fillWidth: true }
                                        FieldLabel { text: "ChArUco 纵向方格数" }
                                        MacSpinBox { id: charucoY; from: 2; to: 30; Layout.fillWidth: true }
                                        FieldLabel { text: "marker 边长 m" }
                                        ModernField { id: markerLength; Layout.fillWidth: true }
                                        FieldLabel { text: "ArUco 字典" }
                                        ModernField { id: dictionary; Layout.fillWidth: true }
                                        FieldLabel { text: "备用 fx / fy" }
                                        RowLayout {
                                            Layout.fillWidth: true
                                            ModernField { id: fx; Layout.fillWidth: true }
                                            ModernField { id: fy; Layout.fillWidth: true }
                                        }
                                        FieldLabel { text: "备用 cx / cy" }
                                        RowLayout {
                                            Layout.fillWidth: true
                                            ModernField { id: cx; Layout.fillWidth: true }
                                            ModernField { id: cy; Layout.fillWidth: true }
                                        }
                                        FieldLabel { text: "畸变参数 D" }
                                        ModernField { id: dist; Layout.fillWidth: true }
                                    }
                                }
                            }

                            MacScrollView {
                                contentWidth: availableWidth
                                ColumnLayout {
                                    width: parent.width
                                    spacing: 16
                                    SectionNote { text: "eye-in-hand 和 eye-to-hand 采样需要查询 base_frame -> tool_frame；camera-to-camera 不需要机械臂 TF。" }
                                    GridLayout {
                                        columns: 2
                                        rowSpacing: 12
                                        columnSpacing: 14
                                        Layout.fillWidth: true
                                        FieldLabel { text: "base_frame" }
                                        ModernField { id: baseFrame; Layout.fillWidth: true }
                                        FieldLabel { text: "tool_frame" }
                                        ModernField { id: toolFrame; Layout.fillWidth: true }
                                        FieldLabel { text: "TF 超时秒数" }
                                        ModernField { id: tfTimeout; Layout.fillWidth: true }
                                    }
                                    PrimaryButton {
                                        text: "刷新 base -> tool TF"
                                        onClicked: root.tfText = backend.refreshTf(root.stateJson())
                                    }
                                    TextArea {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 230
                                        readOnly: true
                                        text: root.tfText
                                        wrapMode: TextArea.Wrap
                                        color: root.textPrimary
                                        background: Rectangle { radius: 12; color: root.fieldBg; border.color: "#D2D2D7" }
                                    }
                                }
                            }

                            MacScrollView {
                                contentWidth: availableWidth
                                ColumnLayout {
                                    width: parent.width
                                    spacing: 16
                                    SectionNote { text: "任务页决定一次采样和一次标定使用哪些输入。建议按 eye-in-hand、eye-to-hand、camera-to-camera 顺序完成。" }
                                    FieldLabel { text: "当前任务" }
                                    MacComboBox {
                                        id: taskBox
                                        model: root.taskNames
                                        Layout.fillWidth: true
                                        onCurrentTextChanged: root.activeTask = currentText
                                    }
                                    SectionNote { text: root.activeTaskHint() }
                                }
                            }

                            MacScrollView {
                                contentWidth: availableWidth
                                ColumnLayout {
                                    width: parent.width
                                    spacing: 16
                                    SectionNote { text: "采样会保存原图、camera_info、检测结果和 annotated.png。若当前任务需要机器人位姿，会同时保存 robot_pose.yaml。" }
                                    GridLayout {
                                        columns: 2
                                        rowSpacing: 12
                                        columnSpacing: 14
                                        Layout.fillWidth: true
                                        FieldLabel { text: "样本编号" }
                                        MacSpinBox { id: sampleId; from: 1; to: 999999; Layout.fillWidth: true }
                                    }
                                    PrimaryButton {
                                        text: "采集当前任务样本"
                                        onClicked: sampleId.value = backend.captureSample(root.stateJson())
                                    }
                                }
                            }

                            MacScrollView {
                                contentWidth: availableWidth
                                ColumnLayout {
                                    width: parent.width
                                    spacing: 16
                                    SectionNote { text: "样本编号 0 表示不限制。eye-to-hand 已知板模式需要填写 T_tool_board：x,y,z,qx,qy,qz,qw。" }
                                    GridLayout {
                                        columns: 2
                                        rowSpacing: 12
                                        columnSpacing: 14
                                        Layout.fillWidth: true
                                        FieldLabel { text: "最小样本编号" }
                                        MacSpinBox { id: minId; from: 0; to: 999999; Layout.fillWidth: true }
                                        FieldLabel { text: "最大样本编号" }
                                        MacSpinBox { id: maxId; from: 0; to: 999999; Layout.fillWidth: true }
                                        FieldLabel { text: "eye-in-hand 方法" }
                                        MacComboBox { id: methodBox; model: ["TSAI", "PARK", "HORAUD", "ANDREFF", "DANIILIDIS"]; Layout.fillWidth: true }
                                        FieldLabel { text: "T_tool_board" }
                                        ModernField { id: tToolBoard; text: "0,0,0,0,0,0,1"; Layout.fillWidth: true }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        PrimaryButton {
                                            text: "运行标定"
                                            Layout.fillWidth: true
                                            onClicked: resultText = backend.runCalibration(root.stateJson())
                                        }
                                        SecondaryButton {
                                            text: "导出 TF"
                                            Layout.fillWidth: true
                                            onClicked: backend.exportTf(root.stateJson())
                                        }
                                    }
                                    TextArea {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 320
                                        readOnly: true
                                        text: resultText
                                        wrapMode: TextArea.Wrap
                                        color: root.textPrimary
                                        font.family: "JetBrains Mono"
                                        font.pixelSize: 12
                                        background: Rectangle { radius: 12; color: root.fieldBg; border.color: "#D2D2D7" }
                                    }
                                }
                            }
                        }
                    }

                    Card {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 130
                        color: "#F5F5F7"
                        TextArea {
                            id: logArea
                            anchors.fill: parent
                            anchors.margins: 10
                            readOnly: true
                            wrapMode: TextArea.Wrap
                            color: "#1D1D1F"
                            font.family: "JetBrains Mono"
                            font.pixelSize: 12
                            background: Rectangle { color: "transparent" }
                        }
                    }
                }
            }
        }

        }

        }

        Rectangle {
            id: startupOverlay
            anchors.fill: parent
            radius: root.frameRadius
            color: "#F5F5F7"
            opacity: root.isBooting ? 1 : 0
            visible: opacity > 0.01
            z: 100
            Behavior on opacity { NumberAnimation { duration: 260; easing.type: Easing.OutCubic } }

            Rectangle {
                anchors.centerIn: parent
                width: 360
                height: 188
                radius: 22
                color: "#FFFFFF"
                border.color: "#E5E5EA"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 26
                    spacing: 16

                    BusyIndicator {
                        Layout.alignment: Qt.AlignHCenter
                        running: root.isBooting
                        implicitWidth: 44
                        implicitHeight: 44
                    }

                    AppText {
                        text: "正在启动标定工具..."
                        Layout.alignment: Qt.AlignHCenter
                        font.pixelSize: 18
                        font.weight: Font.Bold
                    }

                    ProgressBar {
                        id: startupProgress
                        Layout.fillWidth: true
                        from: 0
                        to: 1
                        value: 0.24
                        indeterminate: true
                        background: Rectangle {
                            implicitHeight: 7
                            radius: 4
                            color: "#E5E5EA"
                        }
                        contentItem: Item {
                            id: progressContent
                            property real stripeX: -width * 0.36
                            implicitHeight: 7
                            Rectangle {
                                width: startupProgress.indeterminate ? parent.width * 0.36 : startupProgress.visualPosition * parent.width
                                height: parent.height
                                radius: 4
                                color: root.macBlue
                                x: startupProgress.indeterminate ? parent.stripeX : 0
                                Behavior on width { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
                            }
                            NumberAnimation on stripeX {
                                from: -progressContent.width * 0.36
                                to: progressContent.width
                                duration: 980
                                loops: Animation.Infinite
                                running: startupProgress.indeterminate && root.isBooting
                            }
                        }
                    }

                    AppText {
                        text: "加载配置、相机任务与 Qt 前端资源"
                        Layout.alignment: Qt.AlignHCenter
                        color: root.textSecondary
                        font.pixelSize: 12
                    }
                }
            }
        }
    }
}
