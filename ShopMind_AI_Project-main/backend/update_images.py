import json
from pathlib import Path

# Mapping of specific product_id to realistic, curated, high-quality Unsplash image URLs
PRODUCT_IMAGE_MAP = {
    # LAPTOPS
    "LAP001": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=80", # Sleek silver study laptop
    "LAP002": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=900&q=80", # Pro laptop for dev / dark keyboard
    "LAP003": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?auto=format&fit=crop&w=900&q=80", # Creator workstation laptop
    "LAP004": "https://images.unsplash.com/photo-1541807084-5c52b6b3adef?auto=format&fit=crop&w=900&q=80", # Lightweight travel AirBook
    "LAP005": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?auto=format&fit=crop&w=900&q=80", # High-performance PowerBook
    "LAP006": "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?auto=format&fit=crop&w=900&q=80", # Flexible portable notebook
    "LAP007": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=900&q=80", # WorkMate coding laptop
    "LAP008": "https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?auto=format&fit=crop&w=900&q=80", # UltraBook premium metallic
    "LAP009": "https://images.unsplash.com/photo-1531297484001-80022131f5a1?auto=format&fit=crop&w=900&q=80", # EdgeBook slim design
    "LAP010": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?auto=format&fit=crop&w=900&q=80", # StudioBook designer edition

    # PHONES
    "PHN001": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=900&q=80", # Minimal flagship smartphone
    "PHN002": "https://images.unsplash.com/photo-1598327105666-5b89351aff97?auto=format&fit=crop&w=900&q=80", # Orion Plus large screen phone
    "PHN003": "https://images.unsplash.com/photo-1567581935884-3349723552ca?auto=format&fit=crop&w=900&q=80", # NovaMobile Pro multi-lens camera
    "PHN004": "https://images.unsplash.com/photo-1580910051074-3eb694886505?auto=format&fit=crop&w=900&q=80", # Aster Max vibrant display
    "PHN005": "https://images.unsplash.com/photo-1575695342320-d2d2d2f9b73f?auto=format&fit=crop&w=900&q=80", # ZenMobile Neo slim modern phone
    "PHN006": "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?auto=format&fit=crop&w=900&q=80", # PixelOne Ultra premium black
    "PHN007": "https://images.unsplash.com/photo-1574944985070-8f3ebc6b79d2?auto=format&fit=crop&w=900&q=80", # Orion Air lightweight smartphone
    "PHN008": "https://images.unsplash.com/photo-1585060544812-6b45742d762f?auto=format&fit=crop&w=900&q=80", # NovaMobile Note flagship glass back
    "PHN009": "https://images.unsplash.com/photo-1546054454-aa26e2b734c7?auto=format&fit=crop&w=900&q=80", # Aster Prime executive phone
    "PHN010": "https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?auto=format&fit=crop&w=900&q=80", # ZenMobile Edge curved screen

    # HEADPHONES & AUDIO
    "AUD001": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=80", # Studio over-ear headphones
    "AUD002": "https://images.unsplash.com/photo-1583394838336-acd977736f90?auto=format&fit=crop&w=900&q=80", # SonicArc professional studio wave
    "AUD003": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=900&q=80", # BassPro active noise cancelling
    "AUD004": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&w=900&q=80", # FocusPods true wireless earbuds
    "AUD005": "https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&w=900&q=80", # TravelBeat lightweight audio
    "AUD006": "https://images.unsplash.com/photo-1577174881658-0f30ed549adc?auto=format&fit=crop&w=900&q=80", # SoundFlex foldable headset
    "AUD007": "https://images.unsplash.com/photo-1608156639585-b3a032ef9689?auto=format&fit=crop&w=900&q=80", # PulseX sport wireless earbuds
    "AUD008": "https://images.unsplash.com/photo-1524678606370-a47ad25cb82a?auto=format&fit=crop&w=900&q=80", # ClearSound high fidelity headphones
    "AUD009": "https://images.unsplash.com/photo-1599669454699-248893623440?auto=format&fit=crop&w=900&q=80", # AirBeat on-ear wireless
    "AUD010": "https://images.unsplash.com/photo-1585298723682-7115561c51b7?auto=format&fit=crop&w=900&q=80", # AudioMax DJ monitoring headphones

    # TABLETS
    "TAB001": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&w=900&q=80", # Compact Slate Mini tablet
    "TAB002": "https://images.unsplash.com/photo-1561154464-82e9adf32764?auto=format&fit=crop&w=900&q=80", # NoteTab with digital stylus
    "TAB003": "https://images.unsplash.com/photo-1589739900243-4b52cd9b104e?auto=format&fit=crop&w=900&q=80", # Slim Tab Air tablet
    "TAB004": "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=900&q=80", # ReadMate e-reader tablet
    "TAB005": "https://images.unsplash.com/photo-1585790050230-5dd28404ccb9?auto=format&fit=crop&w=900&q=80", # CanvasTab digital drawing display
    "TAB006": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&w=900&q=80", # Tab Pro aluminum workstation tablet
    "TAB007": "https://images.unsplash.com/photo-1561154464-82e9adf32764?auto=format&fit=crop&w=900&q=80", # StudyTab educational tablet
    "TAB008": "https://images.unsplash.com/photo-1589739900243-4b52cd9b104e?auto=format&fit=crop&w=900&q=80", # MediaTab cinema screen tablet
    "TAB009": "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=900&q=80", # FlexTab convertible tablet
    "TAB010": "https://images.unsplash.com/photo-1585790050230-5dd28404ccb9?auto=format&fit=crop&w=900&q=80", # Tab Plus creator edition

    # MONITORS
    "MON001": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=900&q=80", # VisionView desktop monitor
    "MON002": "https://images.unsplash.com/photo-1585792180666-f7547c67f8b1?auto=format&fit=crop&w=900&q=80", # WorkScreen office monitor
    "MON003": "https://images.unsplash.com/photo-1593642702821-c8da6771f0c6?auto=format&fit=crop&w=900&q=80", # ColorPro calibrated IPS monitor
    "MON004": "https://images.unsplash.com/photo-1547082299-de196ea013d6?auto=format&fit=crop&w=900&q=80", # UltraView 4K monitor setup
    "MON005": "https://images.unsplash.com/photo-1586776977607-310e9c725c37?auto=format&fit=crop&w=900&q=80", # DeskMate ergonomic display
    "MON006": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=900&q=80", # StudioDisplay dual monitor workspace
    "MON007": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&w=900&q=80", # GameView 144Hz gaming monitor
    "MON008": "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=900&q=80", # ClearPanel frameless monitor
    "MON009": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=900&q=80", # WideView ultrawide 21:9 monitor
    "MON010": "https://images.unsplash.com/photo-1585792180666-f7547c67f8b1?auto=format&fit=crop&w=900&q=80", # FocusDisplay productivity monitor

    # KEYBOARDS
    "KEY001": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=900&q=80", # TypePro mechanical keyboard
    "KEY002": "https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?auto=format&fit=crop&w=900&q=80", # Slim wireless KeyBoard Air
    "KEY003": "https://images.unsplash.com/photo-1595225476474-87563907a212?auto=format&fit=crop&w=900&q=80", # MechLite RGB backlight keyboard
    "KEY004": "https://images.unsplash.com/photo-1560762484-813fc97650a0?auto=format&fit=crop&w=900&q=80", # OfficeKeys clean silent keyboard
    "KEY005": "https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?auto=format&fit=crop&w=900&q=80", # QuietType low-profile mechanical keyboard
    "KEY006": "https://images.unsplash.com/photo-1541140532154-b024d705b909?auto=format&fit=crop&w=900&q=80", # GameKeys RGB gaming mechanical
    "KEY007": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=900&q=80", # CompactKeys 65% mini keyboard
    "KEY008": "https://images.unsplash.com/photo-1595225476474-87563907a212?auto=format&fit=crop&w=900&q=80", # ErgoType ergonomic split keyboard
    "KEY009": "https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?auto=format&fit=crop&w=900&q=80", # KeyFlex multi-device bluetooth keyboard
    "KEY010": "https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?auto=format&fit=crop&w=900&q=80", # StudioKeys creator mechanical keyboard

    # MICE
    "MOU001": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?auto=format&fit=crop&w=900&q=80", # Precision ergonomic wireless mouse
    "MOU002": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?auto=format&fit=crop&w=900&q=80", # PrecisionX laser mouse
    "MOU003": "https://images.unsplash.com/photo-1605773527852-c546a8584ea3?auto=format&fit=crop&w=900&q=80", # TravelMouse compact wireless
    "MOU004": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?auto=format&fit=crop&w=900&q=80", # ErgoClick vertical comfort mouse
    "MOU005": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?auto=format&fit=crop&w=900&q=80", # SwiftPoint lightweight mouse
    "MOU006": "https://images.unsplash.com/photo-1605773527852-c546a8584ea3?auto=format&fit=crop&w=900&q=80", # GameClick RGB gaming mouse
    "MOU007": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?auto=format&fit=crop&w=900&q=80", # SilentMouse quiet click switch
    "MOU008": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?auto=format&fit=crop&w=900&q=80", # AirMouse ultra-portable mouse
    "MOU009": "https://images.unsplash.com/photo-1605773527852-c546a8584ea3?auto=format&fit=crop&w=900&q=80", # ControlPro multi-button productivity mouse
    "MOU010": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?auto=format&fit=crop&w=900&q=80", # DeskClick minimal wireless desk mouse

    # SMARTWATCHES
    "WAT001": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=80", # Pulse One smart fitness watch
    "WAT002": "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?auto=format&fit=crop&w=900&q=80", # ActiveFit sport smartwatch
    "WAT003": "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?auto=format&fit=crop&w=900&q=80", # TimePro digital AMOLED smartwatch
    "WAT004": "https://images.unsplash.com/photo-1546868871-7041f2a55e12?auto=format&fit=crop&w=900&q=80", # TrackAir running smart watch
    "WAT005": "https://images.unsplash.com/photo-1510017803434-a899398421b3?auto=format&fit=crop&w=900&q=80", # MoveWatch lifestyle health band
    "WAT006": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=80", # FitEdge sleek heart rate monitor
    "WAT007": "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?auto=format&fit=crop&w=900&q=80", # SportTime rugged waterproof watch
    "WAT008": "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?auto=format&fit=crop&w=900&q=80", # DailyFit daily activity tracker
    "WAT009": "https://images.unsplash.com/photo-1546868871-7041f2a55e12?auto=format&fit=crop&w=900&q=80", # Watch Plus stainless steel luxury smartwatch
    "WAT010": "https://images.unsplash.com/photo-1510017803434-a899398421b3?auto=format&fit=crop&w=900&q=80", # VitalTrack health & sleep monitor

    # CAMERAS
    "CAM001": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=900&q=80", # FrameShot mirrorless camera
    "CAM002": "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?auto=format&fit=crop&w=900&q=80", # CreatorCam vlogging 4K camera
    "CAM003": "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?auto=format&fit=crop&w=900&q=80", # TravelCam compact street camera
    "CAM004": "https://images.unsplash.com/photo-1512790182412-b19e6d62bc39?auto=format&fit=crop&w=900&q=80", # FocusPro professional DSLR camera
    "CAM005": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=900&q=80", # SnapMate instant/point-and-shoot
    "CAM006": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=900&q=80", # StudioCam cine camera setup
    "CAM007": "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?auto=format&fit=crop&w=900&q=80", # ZoomX optical telephoto zoom camera
    "CAM008": "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?auto=format&fit=crop&w=900&q=80", # PocketCam ultra-slim travel camera
    "CAM009": "https://images.unsplash.com/photo-1512790182412-b19e6d62bc39?auto=format&fit=crop&w=900&q=80", # VisionPro 8K mirrorless sensor
    "CAM010": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=900&q=80", # CaptureOne studio camera

    # SPEAKERS
    "SPK001": "https://images.unsplash.com/photo-1545454675-3531b543be5d?auto=format&fit=crop&w=900&q=80", # RoomSound bluetooth speaker
    "SPK002": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?auto=format&fit=crop&w=900&q=80", # MiniBoom portable outdoor speaker
    "SPK003": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?auto=format&fit=crop&w=900&q=80", # BassBox wooden bookshelf studio speaker
    "SPK004": "https://images.unsplash.com/photo-1545454675-3531b543be5d?auto=format&fit=crop&w=900&q=80", # SoundPod round 360 audio speaker
    "SPK005": "https://images.unsplash.com/photo-1517048676732-d65bc937f952?auto=format&fit=crop&w=900&q=80", # PartyBeat high-power wireless speaker
    "SPK006": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?auto=format&fit=crop&w=900&q=80", # DeskSpeaker desktop audio
    "SPK007": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?auto=format&fit=crop&w=900&q=80", # WavePro studio soundbar speaker
    "SPK008": "https://images.unsplash.com/photo-1545454675-3531b543be5d?auto=format&fit=crop&w=900&q=80", # PocketSound pocket clip speaker
    "SPK009": "https://images.unsplash.com/photo-1517048676732-d65bc937f952?auto=format&fit=crop&w=900&q=80", # ClearTone voice clarity speaker
    "SPK010": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?auto=format&fit=crop&w=900&q=80", # BeatBox rugged party speaker
}

def update_product_files():
    backend_path = Path("backend/sample_products.json")
    frontend_path = Path("frontend/data/sample_products.json")

    backend_products = json.loads(backend_path.read_text(encoding="utf-8"))
    
    for p in backend_products:
        pid = p.get("product_id")
        if pid in PRODUCT_IMAGE_MAP:
            p["image_url"] = PRODUCT_IMAGE_MAP[pid]

    updated_json = json.dumps(backend_products, indent=2, ensure_ascii=False)
    backend_path.write_text(updated_json, encoding="utf-8")
    
    frontend_path.parent.mkdir(parents=True, exist_ok=True)
    frontend_path.write_text(updated_json, encoding="utf-8")
    
    print(f"Successfully updated {len(backend_products)} products with specific images in backend and frontend!")

if __name__ == "__main__":
    update_product_files()
