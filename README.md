<!-- PROJECT LOGO 
<br />
<div align="center">
  <a href="https://github.com/othneildrew/Best-README-Template">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>
-->
  <h3 align="center">yapper-bot</h3>

  <p align="center">
    Modular discord bot with chatbot, text transformation, and comment enforcements.
    <br />
   <!-- <a href="https://github.com/othneildrew/Best-README-Template"><strong>Explore the docs »</strong></a> 
    <br />
    <br /> -->
    <a href="https://github.com/adversarial/yapper/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    ·
    <a href="https://github.com/othneildrew/Best-README-Template/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

An entertainment bot with several features such as:
* A fully implemented markov chain chatbot for each server, along with the ability to export .json files for wordclouds or to import into another server. It can be trained on the entire server, individual channels, or passively as messages are sent.
* Comment enforcement "punishments" such as forcing a user to say "I will not plagiarize" for a specified duration or their comment will be removed and a reminder sent, or forcing a user to make their messages longer or shorter for a duration.
* Text transformers such as "owoify" or replacing inappropriate words with safe-for-work versions.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->
## Getting Started


### Prerequisites

This project requires Python 3.8+ and Discord 2.2.0+. The databases are implemented in the nonblocking SQLite wrapper aiosqlite, and numpy is used to `generate weighted random choices for the chatbot.

- discord
 `python3 -m pip install discord`
* numpy
  `python3 -m pip install numpy`
 - aiosqlite
 `python3 -m pip install aiosqlite`

### Installation

To run your own instance, 
- Create a `New Application` on the Discord Developer Portal. 
- Create an access token by clicking `Bot -> Reset Token` and entering your password.
- Enable `Bot -> Privileged Gateway Intents -> Message Content Intent`. 
- Then go to the `Installation" -> "Default Install Settings"` and add `Scopes: bot` and `Permissions: Manage Messages, Read Message History, Read Messages/View Channels.`
-  Open the provided `Install Link` and add the bot to a server. 

- Download this repository
- Save the token you generated in a file named `.secret` in the root directory of the bot. 

- Add your user ID to `owner_ids` array in `config.ini` in the root directory of the bot, e.g. `owner_ids = [ 1234567890, 0987654321 ]`. These users will have access to all administrative features of the bot. To find your user ID, go to `Settings -> Advanced -> Turn On Developer Mode` and then right click on your username in a server, and click `Copy User ID` in the context menu.

- Run the application by executing `python3 main.py` in the root directory of the bot.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- LICENSE -->
## License

Distributed under the GPL 3.0 License. See `LICENSE` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->
## Contact

Project Link: [https://github.com/adversarial/yapper](https://github.com/adversarial/yapper)

<p align="right">(<a href="#readme-top">back to top</a>)</p>
