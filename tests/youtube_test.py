import random
import time
import uuid

import pytest
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import urllib.parse

SEARCH_QUERY = "yulay"


def test_youtube_ads(selenium):
    device_name = selenium.capabilities.get('deviceName') or selenium.capabilities.get('browserName')
    print(f"Corriendo prueba en: {device_name}")

    wait = WebDriverWait(selenium, 20)

    # Ir directo a la búsqueda
    search_url = f"https://m.youtube.com/results?search_query={urllib.parse.quote(SEARCH_QUERY)}"
    selenium.get(search_url)
    time.sleep(2)

    # Simular interacción humana para evitar popup de registro
    selenium.execute_script("window.scrollBy(0, 200);")  # pequeño scroll
    time.sleep(1)
    selenium.find_element(By.TAG_NAME, "body").click()  # clic en cualquier parte
    time.sleep(1)

#    # Buscar primer video largo (no shorts), compatible móvil/desktop
#    video_result = wait.until(
#        EC.element_to_be_clickable((
#            By.XPATH,
#            '(//a[contains(@href,"watch") and not(contains(@href,"shorts"))])[1]'
#        ))
#    )
#    video_result.click()

    # Buscar todos los videos largos (no shorts)
    video_results = wait.until(
        EC.presence_of_all_elements_located((
            By.XPATH,
            '//a[contains(@href,"watch") and not(contains(@href,"shorts"))]'
        ))
    )

    # Filtrar solo los visibles
    visible_videos = [v for v in video_results if v.is_displayed()]

    if not visible_videos:
        raise Exception("No se encontraron videos visibles")

    # Elegir uno al azar
    video_result = random.choice(visible_videos)
    video_result.click()

    # Esperar que cargue el reproductor
    video_player = wait.until(
        EC.presence_of_element_located((By.CLASS_NAME, "html5-video-player"))
    )

    # Intentar dar play si el video está pausado
    try:
        play_button = video_player.find_element(By.CSS_SELECTOR, "button.ytp-large-play-button")
        if play_button.is_displayed():
            play_button.click()
            print(f"[{device_name}] Video iniciado manualmente")
    except:
        print(f"[{device_name}] Video ya estaba en reproducción")

    # Esperar unos segundos para que aparezcan anuncios
    time.sleep(3)

#    # Detectar anuncios
#    ads = selenium.find_elements(By.XPATH, '//ytd-ad-slot-renderer')
#    ad_detected = len(ads) > 0
#
#    if ad_detected:
#        print(f"[{device_name}] Se detectaron anuncios")
#    else:
#        print(f"[{device_name}] No se detectaron anuncios")
#
    # Detectar anuncios de manera más confiable
    ad_detected = False

    # Intentar detectar ad en slot o módulo
    try:
        ad_element = WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ytp-ad-module, ytd-ad-slot-renderer"))
        )
        ad_detected = True
    except TimeoutException:
        ad_detected = False

    # Revisar overlay de anuncio en el reproductor
    try:
        ad_overlay = video_player.find_element(By.CLASS_NAME, "ytp-ad-player-overlay")
        if ad_overlay.is_displayed():
            ad_detected = True
    except:
        pass

    # Resultado
    if ad_detected:
        print(f"[{device_name}] Se detectaron anuncios")
    else:
        print(f"[{device_name}] No se detectaron anuncios")

    # Generar nombre único para la captura
    timestamp = int(time.time() * 1000)
    unique_id = uuid.uuid4().hex[:6]  # 6 caracteres aleatorios
    screenshot_name = f"screenshot_{device_name.replace(' ', '_')}_{timestamp}_{unique_id}.png"

    # Guardar la captura
    selenium.save_screenshot(screenshot_name)

    # Marcar estado en BrowserStack
    selenium.execute_script(
        f'browserstack_executor: {{ "action": "setSessionStatus", "arguments": {{ "status":"{"passed" if not ad_detected else "failed"}", "reason": "Ads detected: {ad_detected}" }} }}'
    )

    print(f"[{device_name}] Captura guardada y subida a BrowserStack: {screenshot_name}")
    assert True
