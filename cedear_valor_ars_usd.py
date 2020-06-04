from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import yfinance as yf
import pandas as pd

def cotizacion_cedears(driver, base_url):

    print('Obteniendo Cotización CEDEARS')
    driver.get(base_url + 'Mercado/Cotizaciones')

    elem = Select(driver.find_element_by_id('paneles'))
    elem.select_by_visible_text('CEDEARs')

    wait = WebDriverWait(driver, 10)
    expected_text = 'Acciones Argentina - Panel CEDEARs'
    selector = (By.ID, 'header-cotizaciones')
    condition = EC.text_to_be_present_in_element(selector, expected_text)
    wait.until(condition)

    select_elem = wait.until(EC.presence_of_element_located((By.XPATH, '//select[@name="cotizaciones_length"]')))
    elem = Select(select_elem)
    elem.select_by_visible_text('Todo')

    table = driver.find_element_by_id('cotizaciones')
    rows = table.find_elements(By.TAG_NAME, 'tr')

    INDEX_TOTAL = 11
    INDEX_SYMBOL = 0
    INDEX_QUOTE = 1

    headers = rows[0].find_elements_by_tag_name('td')
    assert headers[INDEX_SYMBOL].text == 'Símbolo', f'unexpected header name [1]'
    assert headers[INDEX_TOTAL].text == 'Monto\nOperado', f'unexpected header name [2]'
    assert headers[INDEX_QUOTE].text == 'Último\nOperado', f'unexpected header name [3]'
    stocks = list()
    for row in rows[1:-1]:
        cols = row.find_elements_by_tag_name('td')

        name = cols[INDEX_SYMBOL].text.split("\n")[0]
        assert len(name) > 0, f'"{name}" too short'

        volumen = int(cols[INDEX_TOTAL].text.replace('.', ''))
        cotizacion=float(cols[INDEX_QUOTE].text.replace('.', '').replace(',', '.'))


        stocks.append({'volumen': volumen, 'cotizacion': cotizacion, 'name': name})

    driver.close()

    stocks.sort(key=lambda x: x['volumen'],reverse=True)


    return stocks




if __name__ == "__main__":
    
    
    options = FirefoxOptions()
    options.add_argument("--headless")
    #firefox_path = GeckoDriverManager().install()
    driver = webdriver.Firefox(options=options)#, executable_path=firefox_path)
    base_url = 'https://www.invertironline.com/'
    precio_cedear= cotizacion_cedears(driver,base_url)
    precio_cedear_df=pd.DataFrame(precio_cedear).rename(columns={'name': 'Ticker_AR','cotizacion':'precio_ars'})
    
    lista_cedear=pd.read_csv('listado_cedear.txt',sep='\t',encoding='ansi')
    
    cedear_info=pd.merge(lista_cedear,precio_cedear_df,on='Ticker_AR')
    
    cedear_info.columns
    #https://pypi.org/project/yfinance/
    driver.quit()
    my_tickers = lista_cedear['Ticker_NYSE'].to_list()
    stock_data=yf.download(my_tickers,period='1d',interval='15m')['Adj Close']
    
    
    ticker_list=[]
    price_list=[]
    for ticker,price_series in stock_data.iteritems():
        last_valid_index=price_series.last_valid_index()
        if last_valid_index is not None:
            ticker_list.append(ticker)
            price_list.append(price_series[price_series.last_valid_index()])
        
        
    stock_prices=pd.DataFrame({'Ticker_NYSE':ticker_list,'precio_usd':price_list})
     
    all_data=pd.merge(cedear_info,stock_prices, on='Ticker_NYSE') \
        .sort_values(by='volumen',ascending=False)
    all_data['usd_ars']=all_data['Ratio']*all_data['precio_ars']/all_data['precio_usd']



