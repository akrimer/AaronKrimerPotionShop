[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/) [![FastAPI](https://img.shields.io/badge/FastAPI-0.103.0-009688.svg?&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com/) [![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


# Central Coast Cauldrons

Central Coast Cauldrons is a stubbed-out API designed as a starting point for learning how to build backend services that integrate with a persistence layer. You will progressively develop your own version of the API and integrate it with an increasingly sophisticated database backend. When you register your backend at the [Potion Exchange](https://potion-exchange.vercel.app/), simulated customers will shop at your store using your API.

The application is set in a simulated fantasy RPG world where adventurers seek to buy potions. Your shop is one of many in this world, offering a variety of potions with over 100,000 possible combinations.

## Understanding the Game Mechanics

You start with 100 gold, an empty inventory, and no barrels. Your backend API is invoked at regular intervals, called 'ticks,' occurring every two hours. There are 12 ticks per day and 7 days in a week. The weekdays in the Potion Exchange world are:

1. Edgeday
2. Bloomday
3. Aracanaday
4. Hearthday
5. Crownday
6. Blesseday
7. Soulday

Three primary actions occur during these ticks:

1. **Customer Interactions**: On each tick, one or more simulated customers access your catalog endpoint to buy potions. The frequency and timing of customer visits vary by the time of day, and each customer has specific potion preferences. Your shop's performance is evaluated and scored based on multiple criteria (more details on [Potion Exchange](https://potion-exchange.vercel.app/)), influencing how often customers visit.

2. **Potion Creation**: Every other tick presents an opportunity to brew new potions. Each potion requires 100 ml of any combination of red, green, blue, or dark liquid. You must have enough of the chosen liquid in your barrelled inventory to brew a potion.

3. **Barrel Purchasing**: Every other tick, you can purchase additional barrels of various colors. Your API receives a catalog of available barrels and must respond with your purchase decisions. The cost of each barrel is deducted from your balance upon purchase.

Managing your gold and inventory levels effectively is crucial. The [Potion Exchange](https://potion-exchange.vercel.app/) maintains an authoritative record of your shop's stats, which you can view.

### Customers

Customers vary in their shopping habits. Some are more likely to shop on certain days or at specific times. Each customer belongs to a class that significantly influences their potion preferences. The amount a customer is willing to spend depends on their wealth level and how closely the potions match their preferences.

Customers are more likely to visit a shop with a good reputation. You can monitor your shop's reputation at [Potion Exchange](https://potion-exchange.vercel.app/). Reputation is based on four factors:

1. **Value**: Competitive pricing compared to other shops.
2. **Quality**: How well your potions match customer preferences.
3. **Reliability**: Avoiding errors such as checkout failures or listing unavailable potions.
4. **Recognition**: The number of successful purchases by a given customer class. Serving more of a class increases their trust in your shop.

## Initial Setup

Follow these steps to set up your potion shop:

1. **Create a GitHub Repository**
   - Create a new repository by copying the files from this. Do not fork!
   - Name your repository something unique.
   - Make your repository private and grant read access to `jackalnom`.

2. **Deploy on Render**
   - Sign up at [Render](https://render.com/).
   - Click "New +" and select "Web Service."
   - Deploy from your new GitHub repository.
   - Choose a unique and creative name for your service.
   - Select "Oregon" as the region.
   - Leave branch and root directory as default.
   - Set runtime to Python 3.
   - Use `pip install uv && uv pip sync` as the build command.
   - Use `uvicorn src.api.server:app --host 0.0.0.0 --port $PORT` as the start command.
   - Choose the Free Instance Type.
   - Under "Advanced," add two environment variables:
     - `API_KEY`: A unique string to secure your shop's API.
     - `PYTHON_VERSION`: Set to `3.12`.
   - Congratulations you have officially deployed your service to the public cloud! This will be your production instance that is publicly accessible to customers.

3. **Verify Your Deployment**
   - Navigate to `https://[your-project].onrender.com/docs`, replacing `[your-project]` with whatever your project is called.
   - Click 'Authorize' and enter the same `API_KEY` you put into the environment variables above.
   - Test the available endpoints.

4. **Register Your Shop on Potion Exchange**
   - Sign in to [Potion Exchange](https://potion-exchange.vercel.app/).
   - Add your shop with its base URL and `API_KEY`.

5. **Monitor Performance**
   - Return to [Potion Exchange](https://potion-exchange.vercel.app/) to track your shop's progress.
   - Observe changes in gold balance, potion inventory, and customer interactions.

## Running and Testing Locally

To run your server locally:

1. **Set Up Environment Variables**
   - Create a `.env` file in your workspace root.
   - Define `API_KEY` with an easily memorable value for local testing.

2. **Install Dependencies**
   ```sh
   pip install uv && uv pip sync
   ```

3. **Run the Server**
   ```sh
   python main.py
   ```

4. **Test Endpoints**
   - Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
   - Use the interactive documentation to test API endpoints.

5. **Run Tests**
   - Write test cases in the `tests/` folder.
   - Run tests with:
     ```sh
     pytest
     ```

