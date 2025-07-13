from app.ui import build_ui_mock

if __name__ in ("__main__", "__mp_main__"):
    #build_ui().run(port=6789)
    #data = build_ui_mock()
    #print(data)
    build_ui_mock().run(port=6789)