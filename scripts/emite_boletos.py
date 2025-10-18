from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# Configuração do WebDriver
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.108 Safari/537.36")
chrome_options.binary_location = "/usr/bin/google-chrome"

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

try:
    # Acesse a página de login
    driver.get("https://advassessoria.appone.com.br/login/")
    print("Página de login carregada.")

    # Aguarde os campos de login estarem presentes
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))
    username_field = driver.find_element(By.ID, "username")
    password_field = driver.find_element(By.ID, "password")

    # Obter o token CSRF
    csrf_token = driver.find_element(By.NAME, "csrfmiddlewaretoken").get_attribute("value")
    print(f"CSRF Token encontrado: {csrf_token}")

    # Preencha os campos
    username_field.send_keys("admin")
    password_field.send_keys("parceria2010")
    print("Credenciais preenchidas.")

    # Submeta o formulário
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    print("Formulário enviado.")

    # Aguarde redirecionamento após o login
    WebDriverWait(driver, 10).until(EC.url_contains("emitir-boletos"))
    print("Login realizado com sucesso.")

    # Verifique se o login foi bem-sucedido
    if "login" in driver.current_url:
        raise Exception("Login falhou. Verifique as credenciais ou o CSRF token.")

    # Navegar para a página de emissão de boletos
    driver.get("https://advassessoria.appone.com.br/emitir-boletos/")
    print("Navegando para a página de emissão de boletos...")

    # Aguarde o carregamento do formulário
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "emitirBoletoForm")))

    # Localizar botões de emissão
    buttons = driver.find_elements(By.CLASS_NAME, "emitirBoletoButton")
    print(f"{len(buttons)} botões encontrados para emissão de boletos.")

    # Iterar sobre os botões e emitir boletos
    for i, button in enumerate(buttons):
        try:
            # Capturar os atributos necessários
            emitir = button.get_attribute("data-emitir")
            row10 = button.get_attribute("data-row-10")
            row11 = button.get_attribute("data-row-11")
            row12 = button.get_attribute("data-row-12")

            print(f"Emitindo boleto {i + 1} com os dados: Emitir={emitir}, Dias de Atraso={row10}, Valor Recebido={row11}, Comissão={row12}")

            # Preencher os campos ocultos do formulário
            driver.execute_script(f"document.getElementById('emitir').value = `{emitir}`;")
            driver.execute_script(f"document.getElementById('row10').value = `{row10}`;")
            driver.execute_script(f"document.getElementById('row11').value = `{row11}`;")
            driver.execute_script(f"document.getElementById('row12').value = `{row12}`;")

            # Submeter o formulário
            driver.execute_script("document.getElementById('emitirBoletoForm').submit();")

            print(f"Boleto {i + 1} emitido com sucesso.")
            time.sleep(2)  # Tempo entre as emissões
        except Exception as e:
            print(f"Erro ao emitir boleto {i + 1}: {e}")

    print("Processo de emissão de boletos concluído!")

except Exception as e:
    print(f"Erro durante o processo: {e}")

finally:
    driver.quit()
