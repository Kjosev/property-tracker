import requests
from bs4 import BeautifulSoup
import re 
import json

def run(cofig):

    property_divs_map = get_property_divs(config)

    # parse location and price and store in json
    property_divs_map = enrich_property_divs(property_divs_map)

    export_data(property_divs_map)

def export_data(new_data):
    for property in new_data.values():
        property["div"] = None

    # load it up and replace existing ones, adding new ones

    with open('../../datastore/data.json', 'r') as f:
        current_data = json.load(f)

    with open('../../datastore/data.json', 'w') as f:
        for id, property in new_data.items():
            current_data[id] = property

        json.dump(current_data, f)

def enrich_property_divs(property_divs_map):

    for id, property_map in property_divs_map.items():
        address = property_map["div"].find("address").find("span").text
        property_map["address"] = address

        post_code_match = re.search("([^A-Z\d]|^)([A-Z]+\d+[A-Z]?)([^A-Z\d]|$)", address)
        if post_code_match:
            post_code = post_code_match.group(2)
        else:
            post_code = None

        property_map["post_code"] = post_code

        price = property_map["div"].find("span", class_="propertyCard-priceValue").text
        property_map["price"] = float(price[1:-3].replace(",", ""))
        property_map["currency"] = "GBP"

    # for property in property_divs_map.values():
    #     print("ID: {}| Address: {}  | post_code: {}".format(property["id"], property["address"], property["post_code"]))
    #     print(property["price"])

    return property_divs_map

        

def get_property_divs(config):

    property_divs_map = {}
    for page in range(100):
        search_url = get_page(config["search_url"], page)
        print(search_url)

        response = requests.get(search_url)

        soup = BeautifulSoup(response.text, 'html.parser')
        # print(soup.title)

        property_divs = soup.find_all("div", class_="propertyCard")

        found_at_least_one_new = False

        for property_div in property_divs:
            property_id_regex_match = re.search("property-(\d+)", property_div.parent.attrs["id"])
            property_id = property_id_regex_match.group(1)
            
            if property_id == '0':
                # empty card, skipping
                continue
            
            found_at_least_one_new = False
            if property_id not in property_divs_map:
                property_divs_map[property_id] = {
                    "id": property_id,
                    "div": property_div
                }
                found_at_least_one_new = True

        # searching with index greater than the total count returns only empty or old cards so we should end
        if not found_at_least_one_new:
            break

    print("# of found properties: {}".format(len(property_divs_map)))

    return property_divs_map

# page_number 0-indexed
def get_page(search_url, page_number):
    index = 24 * page_number
    return search_url + "&index={index}".format(index=index)


def get_configs():
    # TODO: Clean up site config and preferences/config storage

    location_identifiers = {
        "westminster": "REGION%5E93980"
    }

    sort_types = {
        "newest_listed": 0, # default, any unused number works here
        "oldest_listed": 10,
        "highest_price": 2,
        "lowest_price": 1,
        "keyword_match": 18
    }

    must_haves = {
        "garden": "garden",
        "parking": "parking",
        "student_accomodation": "student",
        "house_share": "houseShare",
        "retirement_home": "retirement"
    }

    dont_show = {
        "student_accomodation": "student",
        "house_share": "houseShare",
        "retirement_home": "retirement"
    }

    furnish_types = {
        "furnished": "furnished",
        "partly_furnished": "partFurnished",
        "unfurnihsed": "unfurnished"
    }

    let_type = {
        "long_term": "longTerm",
        "short_term": "shortTerm",
        "any": None # this potentially applies to all, should see which are required
    }

    search_params = {
        "location": location_identifiers["westminster"],
        "min_bedrooms": 1,
        "max_bedrooms": 3,
        "max_price_gbp": 2500,
        "max_distance_miles": 5.0,
        "sort_type": sort_types["newest_listed"],
        "property_type": "flat",
        "max_days_since_added": 3,
        "include_let_agreed": False,
        "must_haves": "%2C".join([]),
        "dont_show": "%2C".join([dont_show["student_accomodation"], dont_show["retirement_home"], dont_show["house_share"]]),
        "furnish_types": "%2C".join([furnish_types["furnished"], furnish_types["unfurnihsed"], furnish_types["partly_furnished"]]),
        "let_type": let_type["long_term"],
        "keywords": "%2C".join([]),
        "skip_first_n_plus_one": 0 # (0, 24, 48 ...)  futher investigation: available options 0-11 first page, 12-35 second page, 36+ third page (since there were 7 properties) inputing 60 gave me the first page
    }
    print(search_params["location"])

    configs = [
        {
            "site_name": "rightmove",
            "base_url": "https://www.rightmove.co.uk",
            "property_url": "https://www.rightmove.co.uk/properties/{property_id}",
            "search_url": "https://www.rightmove.co.uk/property-to-rent/find.html?locationIdentifier={location}&maxBedrooms={max_bedrooms}&minBedrooms={min_bedrooms}&maxPrice={max_price_gbp}&radius={max_distance_miles}&sortType={sort_type}&propertyTypes={property_type}&maxDaysSinceAdded={max_days_since_added}&includeLetAgreed={include_let_agreed}&mustHave={must_haves}&dontShow={dont_show}&furnishTypes={furnish_types}&letType={let_type}&keywords={keywords}".format(
                location=search_params["location"], max_bedrooms=search_params["max_bedrooms"], min_bedrooms=search_params["min_bedrooms"], max_price_gbp=search_params["max_price_gbp"], max_distance_miles=search_params["max_distance_miles"], sort_type=search_params["sort_type"], property_type=search_params["property_type"], max_days_since_added=search_params["max_days_since_added"], include_let_agreed=search_params["include_let_agreed"], must_haves=search_params["must_haves"], dont_show=search_params["dont_show"], furnish_types=search_params["furnish_types"], let_type=search_params["let_type"], keywords=search_params["keywords"]
            )
        }
    ]

    return configs


if __name__ == "__main__":
    for config in get_configs():
        run(config)