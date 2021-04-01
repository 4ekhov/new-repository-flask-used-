import requests

geocoder_request = "http://geocode-maps.yandex.ru/1.x/?apikey=40d1649f-0493-4b70-98ba-98533de7710b&geocode=Красная пл-дь,1&format=json"
response = requests.get(geocoder_request)

if not response:
    print("Ошибка выполнения запроса:")
    print(geocoder_request)
    print("Http статус:", response.status_code, "(", response.reason, ")")

json_response = response.json()
print(json_response)
toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
toponym_adress = toponym["metaDataProperty"]["GeocoderMetaData"]["text"]
toponym_coodrinates = toponym["Point"]["pos"]
print(toponym_adress)
print(toponym_coodrinates)
