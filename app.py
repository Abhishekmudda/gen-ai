import pandas as pd
import os
from groq import Groq
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import logging
import time
import streamlit as st
from datetime import date

os.system("bash setup.sh")

#db_dir = rdb_dir = r"./chroma_db_directory"
#os.makedirs(db_dir, exist_ok=True)
lamma_new = "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"


def setup_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-notifications')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
def Hotels(checkin_date, checkout_date, location):
    driver = setup_driver()
    hotels_list = []

    def handle_popups():
        popup_selectors = [
            "button[aria-label='Dismiss sign in information.']",
            "button[aria-label='Close']",
            "button.modal-mask-closeBtn",
            "button.closeBtn",
            ".modal-close-button",
            "[data-testid='close-button']",
        ]
        for selector in popup_selectors:
            try:
                close_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                close_button.click()
                time.sleep(0.5)
            except:
                continue

    try:
        url = f"https://www.booking.com/searchresults.en-us.html?checkin={checkin_date}&checkout={checkout_date}&selected_currency=INR&ss={location}&ssne={location}&ssne_untouched={location}&lang=en-us&sb=1&src_elem=sb&src=searchresults&dest_type=city&group_adults=1&no_rooms=1&group_children=0&sb_travel_purpose=leisure"
        driver.get(url)
        time.sleep(3)

        # Handle popups once
        handle_popups()

        # Scroll to load hotels but limit to 25 results
        cards = []
        last_height = driver.execute_script("return document.body.scrollHeight")
        while len(cards) < 25:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            cards = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='property-card']")
            print(f"Loaded {len(cards)} hotels so far.")
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Extract hotel details (limit to 25)
        for idx, card in enumerate(cards[:25]):
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", card)
                time.sleep(0.2)

                hotel_dict = {
                    "id": f"hotels_{idx}",
                    "hotel": WebDriverWait(card, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='title']"))
                    ).text,
                }

                # Get price
                try:
                    price_element = WebDriverWait(card, 5).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "[data-testid='price-and-discounted-price']")
                        )
                    )
                    hotel_dict["price"] = price_element.text
                except:
                    hotel_dict["price"] = "N/A"

                # Get review details
                try:
                    review_score = card.find_element(By.CSS_SELECTOR, "[data-testid='review-score']")
                    hotel_dict["score"] = review_score.find_element(By.CSS_SELECTOR, "div:first-child").text
                    hotel_dict["avg review"] = review_score.find_element(
                        By.CSS_SELECTOR, "div:nth-child(2) > div:first-child"
                    ).text
                    reviews_count = review_score.find_element(
                        By.CSS_SELECTOR, "div:nth-child(2) > div:nth-child(2)"
                    ).text
                    hotel_dict["reviews count"] = reviews_count.split()[0] if reviews_count else "N/A"
                except:
                    hotel_dict.update({"score": "N/A", "avg review": "N/A", "reviews count": "N/A"})

                hotels_list.append(hotel_dict)
            except Exception as e:
                print(f"Error extracting hotel data: {str(e)}")
                continue

    except Exception as e:
        print(f"Error in Hotels function: {str(e)}")
    finally:
        driver.quit()

    return hotels_list

# Attraction Function
def Attraction(location, start_date, country_code):
    driver = setup_driver()
    url = f"https://www.booking.com/attractions/searchresults/{country_code}/{location.lower()}.html?adplat=www-unknown-web_shell_header-attraction-missing_creative-5hMFybjjzTDElUBoJ4LzNc&aid=304142&client_name=b-web-shell-bff&distribution_id=5hMFybjjzTDElUBoJ4LzNc&start_date={start_date}&end_date={start_date}&source=search_box"
    
    try:
        driver.get(url)
        # Explicit wait for elements to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="card"]'))
        )
        
        attractions = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="card"]')
        attractions_list = []
        
        for attraction in attractions[:10]:  # Limit to the first 10
            attraction_dict = {}
            try:
                attraction_dict['attraction_name'] = attraction.find_element(By.CSS_SELECTOR, 'h3[data-testid="card-title"] a').text
            except Exception:
                attraction_dict['attraction_name'] = 'N/A'
            
            try:
                attraction_dict['price'] = attraction.find_element(By.CSS_SELECTOR, 'div[data-testid="price"]').text
            except Exception:
                attraction_dict['price'] = 'N/A'
            
            try:
                attraction_dict['reviews'] = attraction.find_element(By.CSS_SELECTOR, 'div[data-testid="review-score"]').text
            except Exception:
                attraction_dict['reviews'] = 'N/A'
            
            attractions_list.append(attraction_dict)
        
        return attractions_list
    except Exception as e:
        print(f"Error scraping attractions: {str(e)}")
        return []
    finally:
        driver.quit()


def generate_flight_booking_url(departure_airport, arrival_airport, departure_date, adults, children, children_ages, cabin_class="ECONOMY", travel_purpose="leisure"):
    base_url = "https://flights.booking.com/flights/"
    query_params = (
        f"{departure_airport}-"
        f"{arrival_airport}/?type=ONEWAY&"
        f"adults={adults}&"
        f"cabinClass={cabin_class}&"
        f"children={children}&"
        f"from={departure_airport}&"
        f"to={arrival_airport}&"
        f"fromCountry=IN&"
        f"toCountry=IN&"
        f"fromLocationName={departure_airport.replace('.', '+')}+Airport&"
        f"toLocationName={arrival_airport.replace('.', '+')}+Airport&"
        f"depart={departure_date}&"
        f"sort=BEST&"
        f"travelPurpose={travel_purpose}&"
        f"aid=355028&"
        f"label=flights-booking-unknown&"
        f"adplat=www-attractions_index-web_shell_header-flight-missing_creative"
    )
    
    # Append children's ages as comma-separated values
    if children > 0:
        children_ages_param = "&".join([f"childAges[]={age}" for age in children_ages])
        query_params += f"&{children_ages_param}"
    
    return base_url + query_params


# Flight Function
def Flight(url):
    driver = setup_driver()
    try:
        driver.get(url)
        time.sleep(3)
        
        # Scroll to load all flights
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        wait = WebDriverWait(driver, 20)
        flights = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='searchresults_card']")))
        print(f"Found {len(flights)} flights.")
        
        flight_list = []
        for flight in flights:
            driver.execute_script("arguments[0].scrollIntoView(true);", flight)
            time.sleep(0.2)
            
            selectors = {
                'flight': "[data-testid='flight_card_carrier_0']",
                'price': "[data-testid='flight_card_price_main_price']",
                'dep_time': "[data-testid='flight_card_segment_departure_time_0']",
                'arrival_time': "[data-testid='flight_card_segment_destination_time_0']",
                'time_taken': "[data-testid='flight_card_segment_duration_0']",
                'dep_airport': "[data-testid='flight_card_segment_departure_airport_0']",
                'dest_airport': "[data-testid='flight_card_segment_destination_airport_0']"
            }
            
            flight_dict = {}
            for key, selector in selectors.items():
                try:
                    element = flight.find_element(By.CSS_SELECTOR, selector)
                    flight_dict[key] = element.text
                except:
                    flight_dict[key] = 'N/A'
            
            flight_list.append(flight_dict)
        return flight_list
        
    except TimeoutException as e:
        print(f"Timeout error: {str(e)}")
        return []
    except Exception as e:
        print(f"Error: {str(e)}")
        return []
    finally:
        driver.quit()
    

def generate_itinerary(user_query, hotels, flights, attractions):
    # Format each dataset into a structured context for the model
    hotels_context = "\n".join(
        f"- Name: {hotel.get('hotel', 'N/A')}, Price: {hotel.get('price', 'N/A')}, "
        f"Score: {hotel.get('score', 'N/A')}, Reviews: {hotel.get('reviews count', 'N/A')}"
        for hotel in hotels
    )
    
    flights_context = "\n".join(
        f"- Airline: {flight.get('flight', 'N/A')}, Price: {flight.get('price', 'N/A')}, "
        f"Departure: {flight.get('dep_time', 'N/A')} from {flight.get('dep_airport', 'N/A')}, "
        f"Arrival: {flight.get('arrival_time', 'N/A')} at {flight.get('dest_airport', 'N/A')}, "
        f"Duration: {flight.get('time_taken', 'N/A')}"
        for flight in flights
    )
    
    attractions_context = "\n".join(
        f"- Name: {attraction.get('attraction_name', 'N/A')}, Price: {attraction.get('price', 'N/A')}, "
        f"Reviews: {attraction.get('reviews', 'N/A')}"
        for attraction in attractions
    )
    
    # Combine all contexts
    context = (
        "Here is the available data for your trip planning:\n\n"
        f"Hotels:\n{hotels_context}\n\n"
        f"Flights:\n{flights_context}\n\n"
        f"Attractions:\n{attractions_context}\n"
    )

    prompt = (
        "You are a highly knowledgeable Travel Itinerary Generator. Your task is to carefully analyze the context provided "
        "and create a detailed travel itinerary. The data includes hotels, flights, and attractions. Based on the user's preferences "
        "and constraints in the query, choose the most suitable options and plan a complete itinerary.\n\n"
        f"Context:\n{context}\n\n"
        f"Query:\n{user_query}\n\n"
        "Please include the following in the itinerary:\n"
        "- Detailed day-wise schedule with activities, hotel stays based on reviews, and travel.\n"
        "- Mention the selected hotels with check-in and check-out times.\n"
        "- Include flight details such as departure and arrival times.\n"
        "- Highlight recommended attractions for each day.\n"
        "- Suggest meal options or restaurants if possible.\n\n"
        "Provide the output in a clear, structured format.\n"
        "At last based on suggestions provide a total budget of trip"
    )
    # API call to the model
    try:
        client = Groq(api_key=lamma_new)  # Replace with your API key
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.65,
            max_tokens=2048,
            top_p=0.8,
            stream=False,
            stop=None,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error during API call: {str(e)}"

st.title("Travel Itinerary Generator")

with st.sidebar:
    st.header("Trip Details")
    location = st.text_input("Destination", "Paris")
    checkin_date = st.date_input("Check-in Date")
    checkout_date = st.date_input("Check-out Date")
    departure_airport = st.text_input("From Airport", "DEL")
    arrival_airport = st.text_input("To Airport", "CDG")
    departure_date = st.date_input("Flight Date")
    country_code = st.text_input("Country Code", "fr")
    adults = st.number_input("Adults", min_value=1, value=1)
    children = st.number_input("Children", min_value=0, value=0)
    
    if children > 0:
        children_ages = []
        for i in range(children):
            age = st.number_input(f"Child {i+1} Age", min_value=0, max_value=17, value=5)
            children_ages.append(age)
    else:
        children_ages = []
        
    cabin_class = st.selectbox("Cabin Class", ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"])

user_query = st.text_area(
    "Trip Preferences",
    "Plan a family trip including affordable flights, mid-range hotels, and top attractions."
)

# Date validation
today = date.today()
if checkin_date < today:
    st.error("Check-in date cannot be earlier than today's date. Please select a valid date.")
if checkout_date < checkin_date:
    st.error("Check-out date cannot be earlier than the check-in date. Please select a valid date.")
if departure_date < today:
    st.error("Flight date cannot be earlier than today's date. Please select a valid date.")

if st.button("Generate Itinerary", type="primary"):
    with st.spinner("Gathering travel data..."):
        try:
            hotels = Hotels(str(checkin_date), str(checkout_date), location)
            attractions = Attraction(location, str(departure_date), country_code)    
            flight_url = generate_flight_booking_url(departure_airport, arrival_airport, departure_date, adults, children, children_ages, cabin_class)
            flights = Flight(flight_url)
            st.success("Data collection complete!")
            
            with st.spinner("Generating personalized itinerary..."):
                itinerary = generate_itinerary(user_query, hotels, flights, attractions)
                
                st.header("Your Personalized Travel Itinerary")
                st.markdown(itinerary)
                
                with st.expander("View Raw Data"):
                    st.subheader("Hotels")
                    st.write(hotels)
                    st.subheader("Attractions")
                    st.write(attractions)
                    st.subheader("Flights")
                    st.write(flights)
                    
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
