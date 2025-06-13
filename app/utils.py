from geopy import distance as geo_distance


def nearby_filter(user_latitude, user_longitude, stadiums):
    if user_latitude and user_longitude:
        nearby_stadiums = []

        for stadium in stadiums:
            stadium_location = (float(stadium.latitude), float(stadium.longitude))
            user_location = (user_latitude, user_longitude)
            distance = round(geo_distance.distance(user_location, stadium_location).km, 2)

            stadium_data = {
                'id': stadium.id,
                'name': stadium.name,
                'address': stadium.address,
                'contact': stadium.contact,
                'image': stadium.image.url if stadium.image else None,
                'price': stadium.price,
                'distance':distance,
            }
            nearby_stadiums.append(stadium_data)

        nearby_stadiums = sorted(nearby_stadiums, key=lambda x: x['distance'])

        return nearby_stadiums