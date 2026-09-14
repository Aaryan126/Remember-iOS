import Foundation
import CoreGraphics
import ImageIO

let args = CommandLine.arguments
guard args.count == 3, let source = CGImageSourceCreateWithURL(URL(fileURLWithPath: args[1]) as CFURL, nil),
      let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else { fatalError("input image") }
var page = CGRect(x: 0, y: 0, width: image.width, height: image.height)
guard let pdf = CGContext(URL(fileURLWithPath: args[2]) as CFURL, mediaBox: &page, nil) else { fatalError("output PDF") }
pdf.beginPDFPage(nil)
pdf.draw(image, in: page)
pdf.endPDFPage()
pdf.closePDF()
