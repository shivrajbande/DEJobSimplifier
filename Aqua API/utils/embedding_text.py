movies_table_text = '''
Table Name: movies

Purpose:
Stores comprehensive metadata and catalog information about individual movies, including genres, running times, user ratings, financial performance, and release statuses.

Columns:
- Movie_ID: Unique identifier for each movie
- Title: Name/title of the movie
- Primary_Genre: Main genre classification of the movie (e.g., Horror, Action, Sci-Fi)
- Secondary_Genre: Supporting genre classification of the movie (e.g., Crime, Comedy, Drama)
- Release_Year: The calendar year the movie was released
- Runtime_Min: Total duration of the movie in minutes
- IMDb_Rating: Average user rating on IMDb (scale from 1.0 to 10.0)
- Vote_Count: Total number of user votes or ratings submitted on IMDb
- Budget_USD: Estimated production budget of the movie in USD
- Box_Office_USD: Gross worldwide box office revenue in USD
- Language: Primary language spoken in the movie (e.g., Mandarin, Japanese, German)
- Content_Rating: Age-based content classification (e.g., G, PG, R, NC-17)
- Production_Studio: Studio or company responsible for producing the movie (e.g., Netflix, A24, Universal)
- Country: Country of origin or primary filming location (e.g., South Korea, France, Brazil)
- Status: Current phase of the movie's lifecycle (e.g., Released, Post-Production, In Development)

Relationships:
- A movie can feature multiple cast members, directors, and soundtracks
- movies.Movie_ID connects to cast.Movie_ID, directors.Movie_ID, reviews.Movie_ID, awards.Movie_ID, box_office.Movie_ID, streaming.Movie_ID, production.Movie_ID, and soundtracks.Movie_ID

Analytical Usage:
- Used to identify top-performing and highest-rated movies based on audience ratings and vote counts
- Used for financial health and ROI analysis by comparing box office gross revenue against production budgets
- Helps filter and slice movie performance by genre, release year, language, production studio, or content rating

Query Patterns:
- Top-rated movies by primary genre or release year
- Total box office revenue and average budget by production studio
- Count of movies currently in development or post-production phases
'''

persons_table_text = '''
Table Name: persons

Purpose:
Stores biographical and professional performance metrics for industry cast and crew members, tracking their primary roles, credits, accolades, and career statuses.

Columns:
- Person_ID: Unique identifier for each cast or crew member
- First_Name: Given name of the person
- Last_Name: Family name or surname of the person
- Primary_Role: Core professional role within the industry (e.g., Director, Producer, Actor, Writer)
- Date_of_Birth: Birthdate of the individual
- Nationality: Country of origin or citizenship (e.g., Australian, French, Italian)
- Gender: Gender identity of the person (e.g., Male, Female, Non-binary)
- Avg_Rating: Average career performance or project quality rating
- Total_Credits: Total number of industry credits or projects worked on
- Awards_Won: Total count of individual accolades and industry awards won
- Career_Status: Current professional status within the industry (e.g., Active, Retired, Deceased)
- Net_Worth_USD_M: Estimated individual net worth in millions of USD

Relationships:
- A person can participate across multiple movie roles (cast/crew) or win individual awards
- persons.Person_ID connects to cast.Person_ID, directors.Person_ID, and awards.Person_ID

Analytical Usage:
- Used to evaluate talent performance and industry recognition based on average ratings and individual awards won
- Enables demographic and diversity analysis of industry professionals by nationality, gender, and age
- Helps analyze career longevity, professional output (total credits), and financial success relative to career status

Query Patterns:
- Most awarded directors or actors in the industry catalog
- Average net worth and total credits by primary role or nationality
- Active cast or crew members with the highest career average ratings
'''
cast_details_table_text = '''
Table Name: cast_details

Purpose:
Stores intermediate performance and compensation details about actors mapped to specific movie roles, acting as a junction table between movies and persons.

Columns:
- Cast_ID: Unique identifier for each casting entry
- Movie_ID: Reference to the movie the cast member appeared in
- Person_ID: Reference to the person portraying the character
- Character_Name: The name of the character played in the movie
- Character_Type: Classification of the role (e.g., Protagonist, Antagonist, Voice, Cameo)
- Billing_Position: The order in which the actor's name appears in credits (e.g., Lead vs Supporting)
- Screen_Time_Min: Total duration the actor appears on screen in minutes
- Lines_Count: Total number of spoken text lines assigned to the character
- Salary_USD_M: Actor's compensation for the role in millions of USD
- Stunt_Double: Indicator of whether a stunt double was used (Yes/No)
- Fan_Rating: Average audience popularity rating for this specific portrayal
- Award_Nomination: Accolade or award organization nomination received for this performance (e.g., Oscar, SAG, BAFTA)

Relationships:
- Connects movies and persons tables in a many-to-many casting relationship
- cast_details.Movie_ID connects to movies.Movie_ID
- cast_details.Person_ID connects to persons.Person_ID

Analytical Usage:
- Used to calculate financial metrics like average actor payroll relative to project budgets
- Helps analyze character visibility and prominence by tracking screen time against lines count
- Useful for mapping talent popularity (Fan_Rating) to industry accolades (Award_Nomination)

Query Patterns:
- Total cast compensation budget for a specific movie
- Actors with the highest line-to-screen-time efficiency ratio
- Most frequent character types assigned to a specific billing position
'''

directors_table_text = '''
Table Name: directors

Purpose:
Stores tracking details and specific metrics for directors tied to individual movie projects, capturing their stylistic traits and contractual fees.

Columns:
- Director_ID: Unique identifier for each directing credit record
- Movie_ID: Reference to the directed movie
- Person_ID: Reference to the person acting as the director
- Directing_Style: Creative approach or category used (e.g., Documentary, Experimental, Indie, Commercial, Genre)
- Fee_USD_M: Financial payout/fee paid to the director for the movie in millions of USD
- Shooting_Weeks: Number of calendar weeks spent in active production under the director
- Avg_Movie_Rating: Career or historical average rating of movies directed by this person
- Oscar_Wins: Total number of Academy Awards won by the director up to this project
- DGA_Member: Indicator of membership in the Directors Guild of America (Yes/No)
- First_Feature_Year: The calendar year of the director's debut feature-length film
- Total_Films_Directed: Cumulative count of films directed by this person over their career

Relationships:
- Links specific directors from the persons catalog directly to a movie record
- directors.Movie_ID connects to movies.Movie_ID
- directors.Person_ID connects to persons.Person_ID

Analytical Usage:
- Used to benchmark production speed by analyzing shooting weeks against movie metadata
- Useful for comparing director payouts (Fee_USD_M) to total movie ROI and Box Office returns
- Allows categorization of creative outputs based on DGA status and stylistic trends

Query Patterns:
- Directors commanding the highest fees for indie or commercial movies
- Average shooting time in weeks for DGA members versus non-members
- Historical correlation between Oscar wins and a movie's final IMDb rating
'''

reviews_table_text = '''
Table Name: reviews

Purpose:
Stores qualitative and quantitative user feedback, critical opinions, and interaction metrics gathered across various review aggregation platforms.

Columns:
- Review_ID: Unique identifier for each individual review entry
- Movie_ID: Reference to the movie being evaluated
- User_ID: Reference to the registered user or reviewer profile
- Rating: Numeric rating given to the movie by the reviewer
- Sentiment: Evaluated tone of the review text (e.g., Positive, Negative, Neutral, Mixed)
- Platform: Aggregator website where the review was published (e.g., IMDb, Rotten Tomatoes, Metacritic, Google)
- Helpful_Votes: Number of other platform users who flagged the review as helpful
- Comment_Count: Number of reply comments generated on this specific review thread
- Reviewer_Type: Classification of the writer (e.g., Audience, Professional, Critic)
- Review_Date: The calendar date the review was published
- Contains_Spoiler: Indicator of whether text elements reveal major plot points (Yes/No)
- Review_Length_Words: Word count of the submitted review text

Relationships:
- Maps user responses back to specific cinematic pieces
- reviews.Movie_ID connects to movies.Movie_ID
- reviews.User_ID connects to users.User_ID

Analytical Usage:
- Used to observe sentiment drift over time by sorting review dates and sentiment scores
- Helps identify highly influential platform users based on helpful votes and comment counts
- Enables comparative analysis between professional critic ratings and generalized audience scores

Query Patterns:
- Distribution of review sentiment across different publishing platforms
- Most interactive reviews (highest comments/helpful votes) containing spoilers
- Average review length variations between audience reviewers and professional critics
'''

awards_table_text = '''
Table Name: awards

Purpose:
Tracks individual or ensemble accolades, project wins, and prestige benchmarks associated with specific films and attached creators.

Columns:
- Award_ID: Unique identifier for each specific award tracking entry
- Movie_ID: Reference to the film associated with the accolade
- Person_ID: Reference to the individual professional receiving the award (if applicable)
- Award_Name: Name of the organization or award title (e.g., Academy Award, BAFTA, Golden Globe, Cannes Palme d'Or)
- Category: Specific discipline or classification rewarded (e.g., Best Picture, Best Actress, Best Visual Effects, Best Score)
- Year: The calendar year the ceremony took place
- Result: Final outcome of the entry (e.g., Won, Nominated)
- Award_Type: Scope of the recognition tier (e.g., Individual, Film, Crew)
- Ceremony_Number: Sequential iteration count of the specific award body's history
- Prestige_Score: Weighted index score representing the relative industry value of the award (scale up to 100)

Relationships:
- Maps recognized achievements to specific movies and attached persons
- awards.Movie_ID connects to movies.Movie_ID
- awards.Person_ID connects to persons.Person_ID

Analytical Usage:
- Used to determine the overall critical prestige of a film based on its collective prestige scores
- Helps identify career spikes for individuals by aggregating nominations and wins by year
- Enables filtering of movies based on target success categories (e.g., separating acting wins from tech/crew wins)

Query Patterns:
- Total awards won by a film compared to its total nominations
- Individuals holding the highest aggregated prestige score within a single calendar year
- Breakdown of crew-level awards vs individual-level awards for a production studio
'''
box_office_table_text = '''
Table Name: box_office

Purpose:
Stores granular financial performance data and theatrical footprint details for individual movies, tracking initial investments against domestic and international returns.

Columns:
- BoxOffice_ID: Unique identifier for each box office performance record
- Movie_ID: Reference to the associated movie entry
- Production_Budget_USD: The capital invested to produce the movie in USD
- Domestic_Gross_USD: Gross revenue generated in the home or domestic country market in USD
- International_Gross_USD: Gross revenue generated in overseas or international markets in USD
- Worldwide_Gross_USD: Combined global theatrical gross revenue (Domestic + International) in USD
- Theater_Count: Peak or total number of cinemas showcasing the film
- Weeks_in_Theater: Continuous duration the movie remained in active theatrical distribution
- ROI_Ratio: Return on Investment ratio calculated from revenue relative to budget metrics
- Top_Revenue_Region: Geographic market or continent bringing in the highest earnings (e.g., Europe, Latin America)
- Opening_Weekend_Rank: Chart placement rank during the premiere box office weekend
- Marketing_Spend_USD_M: Promotional and advertising expenses in millions of USD

Relationships:
- Connects directly to the main movies catalog via a foreign key relationship
- box_office.Movie_ID connects to movies.Movie_ID

Analytical Usage:
- Used to evaluate financial profitability and success using the ROI ratio and gross revenue margins
- Helps analyze international appeal versus domestic baseline traction across different regions
- Useful for studying marketing elasticity by measuring box office gross against marketing spend

Query Patterns:
- Highest grossing films in specific regions (e.g., top revenue regions)
- Correlation between theater count expansion and total weeks in theater
- Average ROI ratio for projects keeping marketing spend below a target threshold
'''

genre_stats_table_text = '''
Table Name: genre_stats

Purpose:
Stores aggregated, high-level historical performance benchmarks and market trend indexes classified by cinematic genre.

Columns:
- Genre_ID: Unique identifier for each genre tracking entry
- Genre_Name: Descriptive label of the film genre (e.g., Action, Adventure, Biography, Drama)
- Total_Movies: Total historical count of movies assigned to this genre
- Avg_IMDb_Rating: Long-term career or industry average IMDb user rating within this category
- Avg_Budget_USD_M: Normalized historical production budget benchmark in millions of USD
- Avg_Runtime_Min: Average length or duration in minutes for films belonging to this genre
- Year_Established: The approximate milestone year this genre gained industry or classification recognition
- Total_Global_Revenue_USD: Aggregated historical box office gross accumulated by the genre in USD
- Audience_Score: General weighted consumer approval or satisfaction rating index
- Market_Trend: Directional consumer demand indicator (e.g., Growing, Declining, Stable)

Relationships:
- Acts as a standalone reference dimension table for market intelligence
- Maps contextually to fields like movies.Primary_Genre or movies.Secondary_Genre based on string name matches

Analytical Usage:
- Used as a benchmark baseline to check if an individual movie outperforms its standard genre averages
- Helps studios make funding choices by looking at market trends against global revenue parameters
- Useful for identifying consumer taste shifts by contrasting critical ratings with audience scores

Query Patterns:
- Genres displaying growing market trends paired with high audience scores
- Comparative analysis of average runtimes across older vs newer established genres
- Total global revenue rankings of all listed genres
'''

streaming_table_text = '''
Table Name: streaming

Purpose:
Tracks digital distribution agreements, consumption metrics, and licensing states across various subscription video-on-demand (SVOD) platforms.

Columns:
- Stream_ID: Unique identifier for each platform streaming contract record
- Movie_ID: Reference to the movie licensed for digital release
- Platform: The target streaming network hosting the content (e.g., Netflix, Hulu, Apple TV+, Peacock)
- Available_Since: The calendar date the movie became accessible to stream on the platform
- Total_Views: Aggregated view count or play events logged on the platform
- Licensing_Fee_USD_M: Financial amount paid by the platform to license the film in millions of USD
- Days_Trending: Total count of days the title was featured on the platform's top trending arrays
- License_Status: Current contractual state of the asset (e.g., Active, Exclusive, Expired)
- Is_Exclusive: Indicator of whether the platform holds solo streaming rights (Yes/No)
- Watchlist_Adds: Total count of users who saved the title to their custom queue or watchlist
- Platform_Rating: Proprietary internal user score or feedback index logged on that specific platform
- Distribution_Scope: Regional bounds of the distribution rights (e.g., Global, Regional, Country-Specific)

Relationships:
- Connects digital runtime metadata to the movie core index
- streaming.Movie_ID connects to movies.Movie_ID

Analytical Usage:
- Used to track digital footprint lifecycle value by mapping trending days against licensing fees
- Helps calculate streaming engagement velocity using total views relative to availability dates
- Useful for benchmarking platform performance indexes against general IMDb baselines

Query Patterns:
- Platforms holding the most active exclusive global distribution licenses
- Average platform rating variations for a single movie hosted on different services
- Total licensing revenue earned by a production studio across all digital platforms
'''

production_table_text = '''
Table Name: production

Purpose:
Captures behind-the-scenes schedule timelines, technical execution styles, and operational asset budgets allocated during active filming phases.

Columns:
- Prod_ID: Unique identifier for each operational production record
- Movie_ID: Reference to the project being filmed
- Shooting_Start: Calendar date when principal photography began
- Shooting_End: Calendar date when active filming wrapped
- Total_Shoot_Days: Aggregate active workdays spent capturing footage on set
- Filming_Type: Structural logistics format chosen (e.g., On Location, Studios, Mixed)
- Primary_Location: Central geographic country or region where the set was built (e.g., UK, Japan, Germany)
- Crew_Size: Total count of union/non-union crew members and technical staff working on set
- Post_Prod_Budget_USD_M: Financial allocation for editing, coloring, and sound mix in millions of USD
- VFX_Budget_USD_M: Independent subset budget designated for visual effects work in millions of USD
- VFX_Level: Density or demand index of visual effects required (e.g., Minimal, Moderate, Heavy, Extreme)
- CGI_Heavy: Structural indicator of deep reliance on computer-generated imagery (Yes/No)
- Release_Format: Intended display medium or master standard format (e.g., Standard, IMAX, 3D, HDR)

Relationships:
- Anchors physical and technical logistics back to a parent movie listing
- production.Movie_ID connects to movies.Movie_ID

Analytical Usage:
- Used to find post-production bottleneck periods by tracking timespans from shooting end to release dates
- Useful for modeling workforce scaling metrics by studying crew size against total shoot days
- Helps isolate technical cost weights by tracking CGI indicators against VFX budgets

Query Patterns:
- Average shoot duration in days for on-location filming versus studio-bound sets
- Total VFX budget expenditure summary grouped by target release format (e.g., IMAX vs 3D)
- Primary production hubs ranked by total active crew size counts
'''

users_table_text = '''
Table Name: users

Purpose:
Stores account registration profiles, demographic groupings, and general consumption volume metrics for community or app users.

Columns:
- User_ID: Unique identifier for each registered customer or profile
- Username: System handle or display name chosen by the user
- Email: Registered digital contact address linked to the account profile
- Nationality: Demographics country indicator matching user origins (e.g., Italian, British, Spanish)
- Age: Real-time or birth-calculated chronological age of the user
- Gender: Self-identified gender selection (e.g., Male, Female, Non-binary)
- Subscription: Current platform pricing tier level (e.g., Free, Basic, Standard, Premium, Family)
- Join_Date: The calendar date the user account was initialized
- Movies_Watched: Logged tally of films marked as watched or finished by the profile
- Movies_Reviewed: Cumulative count of active text or score reviews submitted by the user
- Fav_Genre: Self-selected or algorithmically derived favorite movie genre choice
- Avg_Rating_Given: Overall mathematical mean of all rating scores left by this user profile

Relationships:
- Serves as the user baseline entity within user engagement tracking
- users.User_ID connects to reviews.User_ID

Analytical Usage:
- Used to build cohort analyses or churn models based on join dates and tier choices
- Helps track community rating biases by filtering user age brackets against average ratings given
- Useful for identifying power users or critics based on high ratios of movies reviewed to watched

Query Patterns:
- Distribution of preferred subscription tiers across different nationalities
- Average count of movies reviewed by users within specified age cohorts
- Correlation between a user's favorite genre and their average rating habits
'''

soundtracks_table_text = '''
Table Name: soundtracks

Purpose:
Stores data regarding audio composition, musical metadata, project investments, and cross-platform streaming stats for official motion picture scores.

Columns:
- Soundtrack_ID: Unique identifier for each soundtrack record
- Movie_ID: Reference to the movie matching the music score
- Composer: The primary musical director or artist credited (e.g., Composer_1, Composer_2)
- Music_Genre: Structural style of the music tracklist (e.g., Jazz, Classical, Ambient, Pop, Orchestral)
- Track_Count: Total number of individual musical audio cuts on the album release
- Total_Duration_Min: Full running time length of the soundtrack album in minutes
- Budget_USD_M: Capital spent creating, mixing, and licensing the music in millions of USD
- Award_Nominations: Total industry music award nominations received for the score
- Oscar_Nominated: Indicator showing if the score received an Academy Award nomination (Yes/No)
- Spotify_Streams: Total audio play counts logged on Spotify for the album tracks
- Critic_Score: Weighted reviewer approval rating score given specifically to the soundtrack audio
- Release_Format: Commercial distribution format options (e.g., CD, Vinyl, Digital, Streaming Only)

Relationships:
- Links audio composition and streaming popularity variables to a parent movie entry
- soundtracks.Movie_ID connects to movies.Movie_ID

Analytical Usage:
- Used to track alternative revenue value by analyzing Spotify stream counts against album budgets
- Helps test critical consensus by reviewing score variables across varying music genres
- Useful for measuring media trends by monitoring vinyl or digital formats against streaming totals

Query Patterns:
- Composers with the highest total Spotify stream counts in ambient or orchestral genres
- Ratios of award nominations achieved per million dollars of soundtrack budget spent
- Distribution of critic scores across vinyl releases compared to streaming-only choices
'''

all_table_texts = {
    "movies": movies_table_text,
    "persons": persons_table_text,
    "cast_details": cast_details_table_text,
    "directors": directors_table_text,
    "reviews": reviews_table_text,
    "awards": awards_table_text,
    "box_office": box_office_table_text,
    "production": production_table_text,
    "streaming": streaming_table_text,
    "soundtracks": soundtracks_table_text,
    "users": users_table_text,
    "genre_stats": genre_stats_table_text,
}