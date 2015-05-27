import qrcode
import qrcode.image.svg
import xml.etree.ElementTree as ET
import io

MAX_QR_CACHE_ENTRIES = 256

class QRImage(qrcode.image.svg.SvgPathFillImage):
    YUU_CACHE = {}
    QR_PATH_STYLE = "fill:#000;fill-opacity:1;fill-rule:nonzero;stroke:none"
    BACKGROUND_COLOUR = "rgba(255,255,255,0.9)"

    def _svg(self, tag="svg", **kwargs):
        svg = super(qrcode.image.svg.SvgImage, self)._svg(tag=tag, **kwargs)
        svg.set("xmlns", self._SVG_namespace)
        svg.append(
            ET.Element("rect", fill=self.BACKGROUND_COLOUR, x="0", y="0",
                       rx="8", ry="8", width="100%", height="100%")
        )
        return svg

    def units(self, units, text=True):
        # Override: specify units in pixels for sharpness.
        if not text:
            return units
        return "{0}px".format(units)

    @classmethod
    def _generate(cls, uri):
        code = qrcode.QRCode(
            version=3,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=5,
            border=3,
            image_factory=cls
        )
        code.add_data(uri)
        svg = code.make_image()
        stream = io.BytesIO()
        svg.save(stream)
        stream.seek(0)
        data = stream.read()
        if len(cls.YUU_CACHE) > MAX_QR_CACHE_ENTRIES:
            cls.YUU_CACHE.popitem()
        cls.YUU_CACHE[uri] = data
        return data

    @classmethod
    def get(cls, address):
        text = "".join(("tox:", address)).lower()
        return cls.YUU_CACHE.get(text, cls._generate(text))
        
