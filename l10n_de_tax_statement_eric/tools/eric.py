# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""A small ctypes binding of the ERiC library of ELSTER.

The library isn't part of this module: its license doesn't allow to pass it
on, every operator downloads it from the ELSTER developer area. See the
ERiC-API-Referenz and the ERiC-Entwicklerhandbuch of the ERiC documentation
for the functions, structures and codes used here.
"""

import ctypes
import os
import threading
from contextlib import contextmanager

# eric_fehlercodes.h
ERIC_OK = 0
ERIC_GLOBAL_PRUEF_FEHLER = 610001002
ERIC_GLOBAL_HINWEISE = 610001003
ERIC_TRANSFER_ERR_XML_THEADER = 610101210
ERIC_TRANSFER_ERR_XML_NHEADER = 610101292
ERIC_CRYPT_E_PIN_WRONG = 610201106

# eric_bearbeitung_flag_t of eric_types.h
ERIC_VALIDIERE = 1 << 1
ERIC_SENDE = 1 << 2
ERIC_DRUCKE = 1 << 5

PDF_CALLBACK = ctypes.CFUNCTYPE(
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.POINTER(ctypes.c_ubyte),
    ctypes.c_uint32,
    ctypes.c_void_p,
)


class DruckParameter(ctypes.Structure):
    """eric_druck_parameter_t, version 4"""

    _fields_ = [
        ("version", ctypes.c_uint32),
        ("vorschau", ctypes.c_uint32),
        ("duplexDruck", ctypes.c_uint32),
        ("pdfName", ctypes.c_char_p),
        ("fussText", ctypes.c_char_p),
        ("pdfCallback", PDF_CALLBACK),
        ("pdfCallbackBenutzerdaten", ctypes.c_void_p),
    ]


class VerschluesselungsParameter(ctypes.Structure):
    """eric_verschluesselungs_parameter_t, version 3"""

    _fields_ = [
        ("version", ctypes.c_uint32),
        ("zertifikatHandle", ctypes.c_uint32),
        ("pin", ctypes.c_char_p),
    ]


# The singlethreading API of ERiC keeps a global state per process
_lock = threading.Lock()


class EricError(Exception):
    def __init__(self, code, message):
        super().__init__(f"{message} ({code})")
        self.code = code
        self.message = message


class EricResult:
    """The outcome of EricBearbeiteVorgang"""

    def __init__(self, code, message, response, server_response, pdfs):
        self.code = code
        self.message = message
        # the XML of rueckgabeXmlPuffer, schema EricBearbeiteVorgang.xsd
        self.response = response
        # the answer of the ELSTER server, only after a transmission
        self.server_response = server_response
        # the PDFs ERiC printed, by their name (Nutzdatenticket or
        # Uebertragungsprotokoll)
        self.pdfs = pdfs

    @property
    def ok(self):
        return self.code in (ERIC_OK, ERIC_GLOBAL_HINWEISE)


class Eric:
    """ERiC loaded from the library file at ``library_path``, e.g.
    ``/opt/ERiC-44.3.6.0/Linux-x86_64/lib/libericapi.so``. The plugins of
    ERiC are searched in the directory of the library. ERiC 44 is required:
    it removed the transferHandle of EricBearbeiteVorgang."""

    def __init__(self, library_path, log_path=None):
        self.library_path = library_path
        self.log_path = log_path
        self.lib = None

    def _load(self):
        if not os.path.isfile(self.library_path):
            raise EricError(None, f"ERiC library not found: {self.library_path}")
        # ERiC requires RTLD_GLOBAL, see "Empfohlenes Vorgehen für Linux"
        lib = ctypes.CDLL(self.library_path, mode=ctypes.RTLD_GLOBAL)
        c_char_p, c_uint32, c_void_p = ctypes.c_char_p, ctypes.c_uint32, ctypes.c_void_p
        lib.EricInitialisiere.argtypes = [c_char_p, c_char_p]
        lib.EricInitialisiere.restype = ctypes.c_int
        lib.EricBeende.argtypes = []
        lib.EricBeende.restype = ctypes.c_int
        lib.EricRueckgabepufferErzeugen.argtypes = []
        lib.EricRueckgabepufferErzeugen.restype = c_void_p
        lib.EricRueckgabepufferInhalt.argtypes = [c_void_p]
        lib.EricRueckgabepufferInhalt.restype = c_char_p
        lib.EricRueckgabepufferFreigeben.argtypes = [c_void_p]
        lib.EricRueckgabepufferFreigeben.restype = ctypes.c_int
        lib.EricHoleFehlerText.argtypes = [ctypes.c_int, c_void_p]
        lib.EricHoleFehlerText.restype = ctypes.c_int
        lib.EricZertifikatOeffnenAusBytes.argtypes = [
            ctypes.POINTER(c_uint32),
            c_char_p,
            c_uint32,
            c_char_p,
        ]
        lib.EricZertifikatOeffnenAusBytes.restype = ctypes.c_int
        lib.EricCloseHandleToCertificate.argtypes = [c_uint32]
        lib.EricCloseHandleToCertificate.restype = ctypes.c_int
        lib.EricBearbeiteVorgang.argtypes = [
            c_char_p,
            c_char_p,
            c_uint32,
            ctypes.POINTER(DruckParameter),
            ctypes.POINTER(VerschluesselungsParameter),
            c_void_p,
            c_void_p,
        ]
        lib.EricBearbeiteVorgang.restype = ctypes.c_int
        return lib

    @contextmanager
    def session(self):
        """Initialize ERiC for one process at a time and end it afterwards"""
        with _lock:
            self.lib = self._load()
            log_path = self.log_path.encode() if self.log_path else None
            code = self.lib.EricInitialisiere(None, log_path)
            if code != ERIC_OK:
                raise EricError(code, self.error_text(code))
            try:
                yield self
            finally:
                self.lib.EricBeende()
                self.lib = None

    def _buffer_content(self, buffer):
        content = self.lib.EricRueckgabepufferInhalt(buffer)
        return content.decode("utf-8", "replace") if content else ""

    def error_text(self, code):
        buffer = self.lib.EricRueckgabepufferErzeugen()
        try:
            self.lib.EricHoleFehlerText(code, buffer)
            return self._buffer_content(buffer)
        finally:
            self.lib.EricRueckgabepufferFreigeben(buffer)

    def process(
        self,
        xml,
        datenart_version,
        flags,
        certificate=None,
        pin=None,
        preview=False,
    ):
        """Validate, print and send the ELSTER XML ``xml`` (bytes) with
        EricBearbeiteVorgang. ``certificate`` is the PKCS#12 container of the
        ELSTER certificate (bytes) with its ``pin``, both only kept in memory.
        """
        pdfs = {}

        def collect_pdf(name, data, size, _user_data):
            pdfs[(name or b"").decode()] = ctypes.string_at(data, size)
            return 0

        callback = PDF_CALLBACK(collect_pdf)
        druck = None
        if flags & ERIC_DRUCKE:
            druck = DruckParameter(
                version=4,
                vorschau=int(preview),
                duplexDruck=0,
                pdfName=None,
                fussText=None,
                pdfCallback=callback,
                pdfCallbackBenutzerdaten=None,
            )
        handle = ctypes.c_uint32(0)
        crypto = None
        response_buffer = self.lib.EricRueckgabepufferErzeugen()
        server_buffer = self.lib.EricRueckgabepufferErzeugen()
        try:
            if certificate:
                code = self.lib.EricZertifikatOeffnenAusBytes(
                    ctypes.byref(handle),
                    certificate,
                    len(certificate),
                    (pin or "").encode(),
                )
                if code != ERIC_OK:
                    raise EricError(code, self.error_text(code))
                crypto = VerschluesselungsParameter(
                    version=3, zertifikatHandle=handle.value, pin=(pin or "").encode()
                )
            code = self.lib.EricBearbeiteVorgang(
                xml,
                datenart_version.encode(),
                flags,
                ctypes.byref(druck) if druck else None,
                ctypes.byref(crypto) if crypto else None,
                response_buffer,
                server_buffer,
            )
            return EricResult(
                code,
                "" if code == ERIC_OK else self.error_text(code),
                self._buffer_content(response_buffer),
                self._buffer_content(server_buffer),
                pdfs,
            )
        finally:
            if handle.value:
                self.lib.EricCloseHandleToCertificate(handle.value)
            self.lib.EricRueckgabepufferFreigeben(response_buffer)
            self.lib.EricRueckgabepufferFreigeben(server_buffer)
