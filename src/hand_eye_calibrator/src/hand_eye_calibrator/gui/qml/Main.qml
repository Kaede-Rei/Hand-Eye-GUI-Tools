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

    Component.onCompleted: {
        loadState(JSON.parse(backend.initialState()))
        appendLog("PySide6 + QML GUI 已启动")
    }

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
        font.family: root.fontStack
        font.pixelSize: 14
        contentItem: AppText {
            text: parent.displayText
            color: root.textPrimary
            verticalAlignment: Text.AlignVCenter
            leftPadding: 12
        }
        background: Rectangle {
            radius: 9
            color: root.fieldBg
            border.color: parent.activeFocus ? root.macBlue : "#D2D2D7"
            border.width: parent.activeFocus ? 2 : 1
        }
        delegate: ItemDelegate {
            width: parent.width
            contentItem: AppText {
                text: modelData
                color: highlighted ? "white" : root.textPrimary
            }
            background: Rectangle {
                color: highlighted ? root.macBlue : "#FFFFFF"
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
            color: btn.down ? root.macBluePressed : btn.hovered ? "#168BFF" : root.macBlue
            Behavior on color { ColorAnimation { duration: 120 } }
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
            color: btn.down ? "#D1D1D6" : btn.hovered ? "#E5E5EA" : "#F2F2F7"
            border.color: "#D2D2D7"
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
        width: parent ? parent.width : 220
        height: 38
        radius: 9
        color: root.currentPage === index ? root.macBlue : navMouse.containsMouse ? "#E8E8ED" : "transparent"
        Behavior on color { ColorAnimation { duration: 130 } }
        AppText {
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: 14
            text: nav.label
            color: root.currentPage === index ? "white" : "#1D1D1F"
            font.pixelSize: 14
            font.weight: root.currentPage === index ? Font.DemiBold : Font.Normal
        }
        MouseArea {
            id: navMouse
            anchors.fill: parent
            hoverEnabled: true
            onClicked: root.currentPage = nav.index
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
        anchors.margins: 18
        radius: 12
        color: root.contentBg
        border.color: "#D2D2D7"
        clip: true

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

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 22
                    spacing: 18

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 14

                        Card {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 250
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
                            Layout.preferredWidth: 330
                            Layout.preferredHeight: 250
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
                            Behavior on opacity { NumberAnimation { duration: 140 } }
                            onCurrentIndexChanged: {
                                opacity = 0.35
                                fadePage.restart()
                            }
                            NumberAnimation {
                                id: fadePage
                                target: stack
                                property: "opacity"
                                to: 1
                                duration: 190
                                easing.type: Easing.OutCubic
                            }

                            ScrollView {
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

                            ScrollView {
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

                            ScrollView {
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

                            ScrollView {
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

                            ScrollView {
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

                            ScrollView {
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

                            ScrollView {
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
