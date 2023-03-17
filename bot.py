import discord
import requests
from discord.ext import commands, tasks
import json

api = ''
faction_id = 1234


def run_discord_bot():
    TOKEN = 'DISCORD TOKEN'
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    
    
    
   
    client = discord.Client(intents=intents)
    bot = commands.Bot(intents=intents, command_prefix="/")

    @tasks.loop(minutes=10)
    async def check():
        global faction_id
        global api
        fac_url = f'https://api.torn.com/faction/{faction_id}?selections=&key={api}'
        response = requests.get(fac_url).json()
        server = client.guilds[0]
        role=discord.utils.get(server.roles, name='TEST ROLE')
        for mem in role.members:
            try:
                memid = mem.display_name.split()[1].strip('[').strip(']')
                if (memid not in response['members']):
                    # print(memid)
                    await mem.remove_roles(role)
                    await mem.edit(nick=mem.name)
            except Exception as e:
                print(e)

        # Check Drug CD
        checkData = {}
        with open('data.json','r') as file:
            checkData = json.load(file)
        
            for id in checkData:
                temp_api = checkData[id]['api']
                try:
                    turl = 'https://api.torn.com/user/?selections=cooldowns&key='+temp_api
                    tresp = requests.get(turl).json()
                   
                    if 'cooldowns' in tresp:
                        if tresp['cooldowns']['drug'] == 0 and checkData[id]['cd'] != 0:
                            tuser = client.get_user(int(id))
                            await tuser.send('Drug CD Expired')
                            checkData[id]['cd'] = int(tresp['cooldowns']['drug'])
                        


                except Exception as e:
                    print(e)
        with open('data.json', 'w') as file:
            json.dump(checkData, file, indent=1)
      


    @client.event
    async def on_ready():
        print(f'{client.user} is now running!')
        check.start()

    @client.event
    async def on_message(message):
        # Make sure bot doesn't get stuck in an infinite loop
        global faction_id
        if message.author == client.user:
            return
        
        
        torn_url = "https://api.torn.com/user/?selections=&key="
        api = ''

        if (message.content.startswith('/notif')):
            user_api = message.content.split()
            if (len(user_api) == 2):
                user_api = user_api[1]
                api_resp = requests.get('https://api.torn.com/user/?selections=cooldowns&key='+user_api).json()
                if 'cooldowns' in api_resp:
                    db_data={}
                    with open('data.json', 'r') as file:
                        db_data = json.load(file)
                    db_data[message.author.id] = {'api':user_api, 'cd':-1}
                    with open('data.json', 'w') as file:
                        db_data = json.dump(db_data, file, indent=1)

                    await message.add_reaction('✅')
                    await message.author.send('Notification Setup Complete! To disable notification, reply with /disable')
                else:
                        message.author.send(api_resp['error']['error'])
                
        if (message.content.startswith('/disable')):
            db_data={}
            with open('data.json', 'r') as file:
                db_data = json.load(file)
            if str(message.author.id) in db_data:
                del db_data[str(message.author.id)]
            
            with open('data.json', 'w') as file:
                db_data = json.dump(db_data,file, indent=1)
            await message.add_reaction('✅')
            await message.author.send("Notification Disabled! To re-enable reply with: /notif API")
        

        
        if (message.content.startswith('/set')):
            print('Setting api')
            print(message)
            user_message = message.content.split()
            api = user_message[1]
            resp =requests.get(torn_url+api).json()
            print(user_message)


            if ('error' in resp):
                await message.channel.send(resp['error']['error'])
            else:
                await message.channel.send(f'{resp["name"]} api set')

        if (message.content.startswith('/faction')):
            try:
                faction_id = int(message.content.split()[1])
                check.start()

            except:
                await message.reply("There was an error!")



        if (message.content.startswith('/verify2')):
            
            url = f'https://api.torn.com/user/ {message.author.id}?selections=discord,profile&key={api}' 
            

            resp = requests.get(url).json()
            
            if ("discord" in resp):
                server = client.get_guild(message.guild.id)
                
                

                try:
                    
                    if ('faction' in resp):
                            if (resp['faction']['faction_id'] == faction_id):
                                role=discord.utils.get(server.roles, name='TEST ROLE')
                                await message.author.add_roles(role,reason='Verified Faction Member')
                            else:
                                role=discord.utils.get(server.roles, name='Verified')
                                await message.author.add_roles(role,reason='Verified Faction Member')

                            
                    await message.author.edit(nick=f'{resp["name"]} [{resp["player_id"]}]')
                    await message.add_reaction('✅')
                except Exception as e:
                    print(e)
                    await message.add_reaction('❌')
                
            else:
                await message.reply(f'Please verify with torn first')
                await message.add_reaction('❌')



                
            



   

    try:
        client.run(TOKEN)
    except KeyboardInterrupt:
        # Properly close the client when the bot is stopped or disconnected
        client.loop.run_until_complete(client.logout())
    finally:
        # Close the event loop
        client.loop.close()
