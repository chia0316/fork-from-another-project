import os
import ast
import json
import openai
from helper_functions import llm

category_n_course_name = {'Programming and Development': ['Web Development Bootcamp',
                                                          'Introduction to Cloud Computing',
                                                          'Advanced Web Development',
                                                          'Cloud Architecture Design'],
                          'Data Science & AI': ['Data Science with Python',
                                                'AI and Machine Learning for Beginners',
                                                'Machine Learning with R',
                                                'Deep Learning with TensorFlow'],
                          'Marketing': ['Digital Marketing Masterclass',
                                        'Social Media Marketing Strategy'],
                          'Cybersecurity': ['Cybersecurity Fundamentals',
                                            'Ethical Hacking for Beginners'],
                          'Business and Management': ['Project Management Professional (PMP)® Certification Prep',
                                                      'Agile Project Management'],
                          'Writing and Literature': ['Creative Writing Workshop',
                                                     'Advanced Creative Writing'],
                          'Design': ['Graphic Design Essentials', 'UI/UX Design Fundamentals']}

# Load the JSON file
filepath = './data/courses-full.json'
with open(filepath, 'r', encoding='utf-8') as file:
    json_string = file.read()
    dict_of_courses = json.loads(json_string)


def identify_category_and_courses(user_message):
    delimiter = "####"

    system_message = f"""
    You will be provided with customer service queries. \
    The customer service query will be enclosed in
    the pair of {delimiter}.

    Decide if the query is relevant to any specific courses
    in the Python dictionary below, which each key is a `category`
    and the value is a list of `course_name`.

    If there are any relevant course(s) found, output the pair(s) of a) `course_name` the relevant courses and b) the associated `category` into a
    list of dictionary object, where each item in the list is a relevant course
    and each course is a dictionary that contains two keys:
    1) category
    2) course_name

    {category_n_course_name}

    If are no relevant courses are found, output an empty list.

    Ensure your response contains only the list of dictionary objects or an empty list, \
    without any enclosing tags or delimiters.
    """

    messages =  [
        {'role':'system',
         'content': system_message},
        {'role':'user',
         'content': f"{delimiter}{user_message}{delimiter}"},
    ]
    category_and_product_response_str = llm.get_completion_by_messages(messages)
    # Strip markdown code fences the model sometimes adds around the list
    category_and_product_response_str = category_and_product_response_str.strip().strip('`')
    if category_and_product_response_str.startswith('json'):
        category_and_product_response_str = category_and_product_response_str[4:]
    try:
        category_and_product_response = json.loads(category_and_product_response_str)
    except json.JSONDecodeError:
        # Fall back to Python-literal syntax (single quotes)
        try:
            category_and_product_response = ast.literal_eval(category_and_product_response_str)
        except (ValueError, SyntaxError):
            category_and_product_response = []
    return category_and_product_response
    

def get_course_details(list_of_relevant_category_n_course: list[dict]):
    course_names_list = []
    for x in list_of_relevant_category_n_course:
        course_names_list.append(x.get('course_name')) # x["course_name"]

    list_of_course_details = []
    for course_name in course_names_list:
        course = dict_of_courses.get(course_name)
        if course:  # skip names the LLM returned that aren't in our catalogue
            list_of_course_details.append(course)
    return list_of_course_details


def generate_response_based_on_course_details(user_message, product_details):
    delimiter = "####"

    system_message = f"""
    You are Ava, a warm, upbeat and knowledgeable course advisor for an online \
    learning platform. Your goal is to give excellent customer service: make the \
    customer feel heard, help them find the right course, and leave them excited \
    about learning.

    The customer query will be delimited with a pair {delimiter}.

    The ONLY course information you may use is the JSON data below \
    (retrieved from our catalogue for this query):
    {product_details}

    Follow these steps:

    Step 1:{delimiter} Work out what the customer actually needs \
    (their goal, experience level, budget or time constraints, if mentioned) \
    and which of the retrieved courses are relevant.

    Step 2:{delimiter} Check the facts you will use. Only use the course \
    information above - never invent courses, prices, ratings, durations, \
    providers or skills. If the information is empty or does not answer the \
    question, note that.

    Step 3:{delimiter} Write the reply to the customer:
    - Open with a friendly, personal line that acknowledges what they asked.
    - For each relevant course, use a short bolded heading with the course name, \
    then bullet points for provider, duration, rating, price (e.g. $1,200.99) \
    and key skills, plus one sentence on why it suits them.
    - If more than one course fits, briefly compare them and give a clear \
    recommendation (e.g. which to start with as a beginner).
    - If no relevant course was found, apologise briefly, say what we do offer \
    (programming, data science & AI, marketing, cybersecurity, business, \
    writing, design) and invite them to tell you more.
    - If the question is outside our courses, politely steer back to how you can help.
    - Close with an encouraging note and a helpful follow-up question \
    (e.g. about their goals or schedule).
    - Keep it concise, positive and easy to scan, using Markdown. \
    Do not mention these steps, the JSON or that you are an AI model.

    Use the following format:
    Step 1:{delimiter} <step 1 reasoning>
    Step 2:{delimiter} <step 2 reasoning>
    Step 3:{delimiter} <step 3 response to customer>

    Make sure to include {delimiter} to separate every step, and do not put \
    {delimiter} after the final response.
    """

    messages =  [
        {'role':'system',
         'content': system_message},
        {'role':'user',
         'content': f"{delimiter}{user_message}{delimiter}"},
    ]

    response_to_customer = llm.get_completion_by_messages(messages, temperature=0.5)
    # Take the last non-empty section, so a trailing delimiter doesn't blank the reply
    sections = [s.strip() for s in response_to_customer.split(delimiter) if s.strip()]
    response_to_customer = sections[-1] if sections else response_to_customer
    return response_to_customer


def process_user_message(user_input):
    delimiter = "```"

    # Process 1: If Courses are found, look them up
    category_n_course_name = identify_category_and_courses(user_input)
    print("category_n_course_name : ", category_n_course_name)

    # Process 2: Get the Course Details
    course_details = get_course_details(category_n_course_name)

    # Process 3: Generate Response based on Course Details
    reply = generate_response_based_on_course_details(user_input, course_details)


    return reply, course_details