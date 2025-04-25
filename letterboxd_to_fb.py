"""
Function that takes in movies that I watched in a certain month, outputs in a Facebook post format
"""

from openai import OpenAI
import openai
import os
from dotenv import load_dotenv
import pandas as pd 
from datetime import datetime
import argparse

def letterboxd_to_fb(df, month, year, prompts):
    # only get the reviews in the specific timeframe
    df["Watched Date"] = pd.to_datetime(df["Watched Date"])
    mask = (df["Watched Date"].dt.year == year) & (df["Watched Date"].dt.month == month)
    df = df[mask]
    for ind,row in df.iterrows():
        review = row["Review"]
        # anything greater than or equal to 3.0 stars is a positive review
        if row["Rating"] >= 3.0:
            thumbs = "(Yes)"
        else:
            thumbs = "(No)"
        summary = summarize_review(review, prompts)
        print("")
        print(row["Name"] + " " + thumbs)
        print(summary)


# clean up reviews
def preprocessing(review):
    review = review.replace('\xa0', ' ').replace('\r', ' ').replace('\n', ' ')
    review = review.replace('<i>', '').replace('</i>', '')
    return review

# generate the summary for the review
def summarize_review(review, prompts, model="gpt-4o", max_tokens=150):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": f"You are a helpful assistant that summarizes movie reviews within one to four sentences. \
             Summarize in the first person, expressing the viewpoints as if they are your own. \
             Summarize movie reviews in the same style as these examples: {prompts} "},
            {"role": "user", "content": review}
        ],        
        max_tokens=max_tokens,
    )

    # Extracting the summary from the response
    return response.choices[0].message.content

# add optional arguments for month and year to utilize
def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch and post last-month’s Letterboxd reviews (or a month/year you supply)."
    )
    parser.add_argument(
        "-m", "--month",
        type=int, choices=range(1, 13),
        help="Month to process (1–12)."
    )
    parser.add_argument(
        "-y", "--year",
        type=int,
        help="Year to process (e.g. 2025)."
    )
    return parser.parse_args()

if __name__ == "__main__":
    # 1) parse CLI args
    args = parse_args()
    
    # import API KEY from .env
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # get dates
    if args.month is not None and args.year is not None:
        month = args.month
        year  = args.year
    else:
        now = datetime.now()
        if now.month == 1:
            month = 12
            year = now.year - 1
        else:
            month = now.month - 1
            year = now.year

    # get review dataframe
    df = pd.read_csv("data/reviews.csv")

    # get trainable prompts and summaries
    review_ml = preprocessing(df[df["Name"]=="Missing Link"]["Review"].values[0])
    summary_ml = "A fun animated story. Great stop-motion visual effects, but most people probably won't know it's stop-motion to appreciate it."
    review_rd = preprocessing(df[df["Name"]=="Reservoir Dogs"]["Review"].values[0])
    summary_rd = "Tarantino's first feature-length debut lies strongly along the rest of his filmography. Somehow, seeing the physical and mental effects of a bank heist on criminals was way more fascinating than seeing the actual bank heist - that is the power of a strong screenplay. Nonlinear storytelling was executed effectively, and not just as a schtick."
    review_2001 = preprocessing(df[df["Name"]=="2001: A Space Odyssey"]["Review"].values[0])
    summary_2001 = "This is the prime example of film as art. Every frame was meticulously crafted, coming together to generate cinematic hypnotism. Despite being over 50 years old, it is still a masterpiece on current standards – I never felt that the visuals were limited by the filmmaking technology available at the time. This is also one of the most terrifying movies I’ve ever watched. No other film like this exists."
    review_ag = preprocessing(df[df["Name"]=="American Graffiti"]["Review"].values[0])
    summary_ag = "I’m glad this movie was successful to give George Lucas the power to make Star Wars. But I think this movie would only resonate well to people that were in their teenage years in the 1960s."
    review_vn = preprocessing(df[df["Name"]=="Violent Night"]["Review"].values[0])
    summary_vn = "Die Hard with David Harbour as Santa. On paper, this should be perfect for me: I’m a sucker for action thrillers and anything Christmas. But, I disagreed with every plot choice and there were many inconsistencies that gave me more frustration than enjoyment."
    prompts = f"\n\nExample Review: {review_ml}" + \
        f"\nExample Summary: {summary_ml}" + \
        f"\n\nExample Review: {review_rd}" + \
        f"\nExample Summary: {summary_rd}" + \
        f"\n\nExample Review: {review_2001}" + \
        f"\nExample Summary: {summary_2001}" + \
        f"\n\nExample Review: {review_ag}" + \
        f"\nExample Summary: {summary_ag}" + \
        f"\n\nExample Review: {review_vn}" + \
        f"\nExample Summary: {summary_vn}" 


    letterboxd_to_fb(df, month, year, prompts)
    