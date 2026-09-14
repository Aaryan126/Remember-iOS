import Foundation
import CoreGraphics
import CoreText
import ImageIO
import UniformTypeIdentifiers

// Code-native test document, not a user image or a visual design asset.
let args = CommandLine.arguments
guard args.count == 5, let text = try? String(contentsOfFile: args[1], encoding: .utf8) else {
    fatalError("usage: render-fixture text.txt output.png|pdf clean|degraded seed")
}
let output = URL(fileURLWithPath: args[2])
let degraded = args[3] == "degraded"
let seed = Int(args[4]) ?? 0
var page = CGRect(x: 0, y: 0, width: 900, height: 1200)
func draw(_ context: CGContext) {
    context.setFillColor(CGColor(gray: degraded ? 0.93 : 1, alpha: 1))
    context.fill(page)
    context.saveGState()
    if degraded {
        context.translateBy(x: 18, y: 6)
        context.rotate(by: 0.015)
    }
    let font = CTFontCreateWithName("Helvetica" as CFString, degraded ? 22 : 26, nil)
    let attributes: [NSAttributedString.Key: Any] = [
        NSAttributedString.Key(kCTFontAttributeName as String): font,
        NSAttributedString.Key(kCTForegroundColorAttributeName as String): CGColor(gray: degraded ? 0.36 : 0.08, alpha: 1)
    ]
    let string = NSAttributedString(string: text, attributes: attributes)
    let framesetter = CTFramesetterCreateWithAttributedString(string)
    let path = CGPath(rect: page.insetBy(dx: 65, dy: 90), transform: nil)
    CTFrameDraw(CTFramesetterCreateFrame(framesetter, CFRange(location: 0, length: 0), path, nil), context)
    context.restoreGState()
    if degraded {
        context.setStrokeColor(CGColor(gray: 0.5, alpha: 0.12))
        for i in 0..<25 {
            let y = CGFloat((i * 47 + seed * 31) % 1200)
            context.move(to: CGPoint(x: 0, y: y))
            context.addLine(to: CGPoint(x: 900, y: y + 2))
        }
        context.strokePath()
    }
}
if output.pathExtension == "pdf" {
    guard let context = CGContext(output as CFURL, mediaBox: &page, nil) else { fatalError("PDF context") }
    context.beginPDFPage(nil)
    draw(context)
    context.endPDFPage()
    context.closePDF()
} else {
    guard let context = CGContext(data: nil, width: 900, height: 1200, bitsPerComponent: 8, bytesPerRow: 0,
                                  space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { fatalError("bitmap") }
    draw(context)
    guard let image = context.makeImage(), let writer = CGImageDestinationCreateWithURL(output as CFURL, UTType.png.identifier as CFString, 1, nil) else { fatalError("PNG writer") }
    CGImageDestinationAddImage(writer, image, nil)
    guard CGImageDestinationFinalize(writer) else { fatalError("PNG save") }
}
