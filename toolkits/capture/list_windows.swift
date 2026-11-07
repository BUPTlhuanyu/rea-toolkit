// 列出指定 App 的所有普通窗口（layer 0），包含位于其他 Space、被遮挡、未激活的窗口。
//
// 存在的理由：`screencapture -R <区域>` 截的是屏幕画面，一旦用户切换 Space 或点了别的窗口，
// 截到的就是别人的画面。改成 `screencapture -l <窗口ID>` 抓窗口自身图层后，截图不再要求
// 目标窗口在前台，整个流程可以在用户正常使用机器时后台跑完。窗口 ID 只能从
// CGWindowList 取，故有此脚本。
//
// 用法：list-windows [App 名子串]        // 子串不区分大小写，省略则列出全部
// 输出：每行 `窗口ID \t 是否在屏 \t 宽 \t 高 \t 标题`（制表符分隔，标题可能为空）
//
// 权限：CGWindowList 不需要「辅助功能」授权；后续截图需要「屏幕录制」授权。
import CoreGraphics
import Foundation

let needle = (CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "").lowercased()

// .optionAll 而非 .optionOnScreenOnly：后者会漏掉其他 Space 上的窗口，而那正是要截的对象。
guard let windows = CGWindowListCopyWindowInfo([.optionAll, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] else {
    FileHandle.standardError.write("无法读取窗口列表（可能缺少「屏幕录制」授权）\n".data(using: .utf8)!)
    exit(1)
}

func pixels(_ bounds: [String: Any], _ key: String) -> Int {
    Int((bounds[key] as? NSNumber)?.doubleValue ?? 0)
}

for window in windows {
    // layer 0 是普通文档/对话框窗口；菜单栏、悬浮层、Dock 图标在其他层。
    guard (window[kCGWindowLayer as String] as? Int) == 0 else { continue }
    let owner = (window[kCGWindowOwnerName as String] as? String ?? "").lowercased()
    guard needle.isEmpty || owner.contains(needle) else { continue }

    let id = window[kCGWindowNumber as String] as? Int ?? 0
    let onscreen = (window[kCGWindowIsOnscreen as String] as? Bool ?? false) ? "1" : "0"
    let bounds = window[kCGWindowBounds as String] as? [String: Any] ?? [:]
    let title = window[kCGWindowName as String] as? String ?? ""
    print("\(id)\t\(onscreen)\t\(pixels(bounds, "Width"))\t\(pixels(bounds, "Height"))\t\(title)")
}
