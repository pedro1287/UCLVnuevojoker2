from pyobigram.utils import sizeof_fmt,get_file_size,createID,nice_time
from pyobigram.client import ObigramClient,inlineQueryResultArticle
from MoodleClient import MoodleClient
from JDatabase import JsonDatabase
import zipfile
import os
import infos
import xdlink
import mediafire
import datetime
import time
import youtube
import NexCloudClient
from pydownloader.downloader import Downloader
from ProxyCloud import ProxyCloud
import ProxyCloud
import socket
import S5Crypto
import random
####################################################
saveconfig = "✅Configuración Guardada"
proxy_list = []
###################################################


#ef nameRamdom():
   # populaton = 'abcdefgh1jklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ'
   # name = "".join(random.sample(populaton,10))
   # return name
def downloadFile(downloader,filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        thread = args[2]
        if thread.getStore('stop'):
            downloader.stop()
        downloadingInfo = infos.createDownloading(filename,totalBits,currentBits,speed,time,tid=thread.id)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: print(str(ex))
    pass

def uploadFile(filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        originalfile = args[2]
        thread = args[3]
        downloadingInfo = infos.createUploading(filename,totalBits,currentBits,speed,time,originalfile)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: print(str(ex))
    pass

def processUploadFiles(filename,filesize,files,update,bot,message,thread=None,jdb=None):
    try:
        bot.editMessageText(message,'📡Conectando con el servidor')
        evidence = None
        fileid = None
        user_info = jdb.get_user(update.message.sender.username)
        cloudtype = user_info['cloudtype']
        proxy = ProxyCloud.parse(user_info['proxy'])
        if cloudtype == 'moodle':
            client = MoodleClient(user_info['moodle_user'],
                                  user_info['moodle_password'],
                                  user_info['moodle_host'],
                                  user_info['moodle_repo_id'],
                                  proxy=proxy)
            loged = client.login()
            itererr = 0
            if loged:
                if user_info['uploadtype'] == 'evidence':
                    evidences = client.getEvidences()
                    evidname = str(filename).split('.')[0]
                    for evid in evidences:
                        if evid['name'] == evidname:
                            evidence = evid
                            break
                    if evidence is None:
                        evidence = client.createEvidence(evidname)

                originalfile = ''
                if len(files)>1:
                    originalfile = filename
                draftlist = []
                for f in files:
                    f_size = get_file_size(f)
                    resp = None
                    iter = 0
                    tokenize = False
                    if user_info['tokenize']!=0:
                       tokenize = True
                    while resp is None:
                          if user_info['uploadtype'] == 'evidence':
                             fileid,resp = client.upload_file(f,evidence,fileid,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'draft':
                             fileid,resp = client.upload_file_draft(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'blog':
                             fileid,resp = client.upload_file_blog(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'calendario':
                             fileid,resp = client.upload_file_calendar(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'calendarioevea':
                             fileid,resp = client.upload_file_calendarevea(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                             draftlist.append(resp)
                          iter += 1
                          if iter>=10:
                              break
                    os.unlink(f)
                if user_info['uploadtype'] == 'evidence':
                    try:
                        client.saveEvidence(evidence)
                    except:pass
                return draftlist
            else:
                bot.editMessageText(message,'⚠ Hubo un error ⚠')
        elif cloudtype == 'cloud':
            tokenize = False
            if user_info['tokenize']!=0:
               tokenize = True
            bot.editMessageText(message,'Subiendo ☁ Espere Mientras... ')
            host = user_info['moodle_host']
            user = user_info['moodle_user']
            passw = user_info['moodle_password']
            remotepath = user_info['dir']
            client = NexCloudClient.NexCloudClient(user,passw,host,proxy=proxy)
            loged = client.login()
            if loged:
               originalfile = ''
               if len(files)>1:
                    originalfile = filename
               filesdata = []
               for f in files:
                   data = client.upload_file(f,path=remotepath,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                   filesdata.append(data)
                   os.unlink(f)
               return filesdata
        return None
    except Exception as ex:
        bot.editMessageText(message,'Error\n' + str(ex))
        return None


def processFile(update,bot,message,file,obten_name,thread=None,jdb=None):
    file_size = get_file_size(file)
    ext = file.split('.')[-1]
    if '7z.' in file:
        ext1 = file.split('.')[-2]
        ext2 = file.split('.')[-1]
        name = obten_name + '.'+ext1+'.'+ext2
        
    else:
        name = obten_name + '.'+ext
        
    os.rename(file,name)
    print(name)
    getUser = jdb.get_user(update.message.sender.username)
    max_file_size = 1024 * 1024 * getUser['zips']
    file_upload_count = 0
    client = None
    findex = 0
    if file_size > max_file_size:
        compresingInfo = infos.createCompresing(name,file_size,max_file_size)
        bot.editMessageText(message,compresingInfo)
        #zipname = str(name).split('.')[0] + createID()
        zipname = str(name).split('.')[0]
        mult_file = zipfile.MultiFile(zipname,max_file_size)
        zip = zipfile.ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
        zip.write(name)
        zip.close()
        mult_file.close()
        client = processUploadFiles(name,file_size,mult_file.files,update,bot,message,jdb=jdb)
        try:
            os.unlink(name)
        except:pass
        file_upload_count = len(zipfile.files)
    else:
        client = processUploadFiles(name,file_size,[name],update,bot,message,jdb=jdb)
        file_upload_count = 1
    bot.editMessageText(message,'Preparando Archivo ...')
    evidname = ''
    files = []
    if client:
        if getUser['cloudtype'] == 'moodle':
            if getUser['uploadtype'] == 'evidence':
                try:
                    evidname = str(name).split('.')[0]
                    txtname = evidname + '.txt'
                    evidences = client.getEvidences()
                    for ev in evidences:
                        if ev['name'] == evidname:
                           files = ev['files']
                           break
                        if len(ev['files'])>0:
                           findex+=1
                    client.logout()
                except:pass
            if getUser['uploadtype'] == 'draft' or getUser['uploadtype'] == 'blog' or getUser['uploadtype']=='calendario' or getUser['uploadtype']=='calendarioevea':
               for draft in client:
                   files.append({'name':draft['file'],'directurl':draft['url']})
        else:
            for data in client:
                files.append({'name':data['name'],'directurl':data['url']})
        bot.deleteMessage(message.chat.id,message.message_id)
        #finishInfo = infos.createFinishUploading(name,file_size,max_file_size,file_upload_count,file_upload_count,findex)
        finishInfo = infos.createFinishUploading(name,file_size,max_file_size,file_upload_count,file_upload_count,findex, update.message.sender.username)
        filesInfo = infos.createFileMsg(name,files)
        bot.sendMessage(message.chat.id,finishInfo+'\n'+filesInfo,parse_mode='html')
        bot.sendMessage(ID DEL CANAL DE LOG,finishInfo+'\n'+filesInfo,parse_mode='html')
        if len(files)>0:
            txtname = str(name).split('/')[-1].split('.')[0] + '.txt'
            sendTxt(txtname,files,update,bot)
    else:
        bot.editMessageText(message,'⚠ Hubo un error ⚠')

def ddl(update,bot,message,url,obten_name,file_name='',thread=None,jdb=None):
    downloader = Downloader()
    file = downloader.download_url(url,progressfunc=downloadFile,args=(bot,message,thread))
    if not downloader.stoping:
        if file:
            processFile(update,bot,message,file,obten_name,jdb=jdb)
        # else:
        #     megadl(update,bot,message,url,file_name,thread,jdb=jdb)

# def megadl(update,bot,message,megaurl,file_name='',thread=None,jdb=None):
#     megadl = megacli.mega.Mega({'verbose': True})
#     megadl.login()
#     try:
#         info = megadl.get_public_url_info(megaurl)
#         file_name = info['name']
#         megadl.download_url(megaurl,dest_path=None,dest_filename=file_name,progressfunc=downloadFile,args=(bot,message,thread))
#         if not megadl.stoping:
#             processFile(update,bot,message,file_name,thread=thread)
#     except:
#         files = megaf.get_files_from_folder(megaurl)
#         for f in files:
#             file_name = f['name']
#             megadl._download_file(f['handle'],f['key'],dest_path=None,dest_filename=file_name,is_public=False,progressfunc=downloadFile,args=(bot,message,thread),f_data=f['data'])
#             if not megadl.stoping:
#                 processFile(update,bot,message,file_name,thread=thread)
#         pass
#     pass

def sendTxt(name,files,update,bot):
                txt = open(name,'w')
                fi = 0
                for f in files:
                    separator = ''
                    if fi < len(files)-1:
                        separator += '\n'
                    txt.write(f['directurl']+separator)
                    fi += 1
                txt.close()
                bot.sendFile(update.message.chat.id,name)
                bot.sendFile(aqui el mismo id del canal,name)
                os.unlink(name)

def onmessage(update,bot:ObigramClient):
    try:
        thread = bot.this_thread
        username = update.message.sender.username
        tl_admin_user = os.environ.get('AQUI TU USER SIN @')

        #Descomentar debajo solo si se ba a poner el usuario admin de telegram manual
        tl_admin_user = 'AQUI TU USER SIN @'

        jdb = JsonDatabase('database')
        jdb.check_create()
        jdb.load()

        user_info = jdb.get_user(username)

        if username == tl_admin_user or user_info:  # validate user
            if user_info is None:
                if username == tl_admin_user:
                    jdb.create_admin(username)
                else:
                    jdb.create_user(username)
                user_info = jdb.get_user(username)
                jdb.save()
        else:
            mensaje = "Usted no tiene acceso.\nPor favor Contacta con mi Programador @"+"AQUI_TU_USER"+"/n"
            intento_msg = "💢El usuario @"+username+ " ha intentando usar el bot sin permiso💢"
            bot.sendMessage(update.message.chat.id,mensaje)
            bot.sendMessage(Aqui el mismo id del canal,intento_msg)
            return


        msgText = ''
        try: msgText = update.message.text
        except:pass

        # comandos de admin
        if '/adduser' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
            #getUser = user_info
            #if getUser:    
                try:
                    user = str(msgText).split(' ')[1]
                    jdb.create_user(user)
                    jdb.save()
                    msg = ' @'+user+' ahora tiene acceso al bot'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,'Error en el comando /adduser username')
            else:
                bot.sendMessage(update.message.chat.id,'No Tiene Permiso')
            return
        if '/banuser' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    if user == username:
                        bot.sendMessage(update.message.chat.id,'❌No Se Puede Banear Usted❌')
                        return
                    jdb.remove(user)
                    jdb.save()
                    msg = '🦶Fuera @'+user+' Baneado❌'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,'Error en el comando /banuser username')
            else:
                bot.sendMessage(update.message.chat.id,'No Tiene Permiso')
            return
        if '/getdb' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
            #getUser = user_info
            #if getUser:    
                bot.sendMessage(update.message.chat.id,'Base De Datos👇')
                bot.sendFile(update.message.chat.id,'database.jdb')
            else:
                bot.sendMessage(update.message.chat.id,'No Tiene Permiso')
            return
        if '/viewdb' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                db = open('database.jdb','r')
                bot.sendMessage(update.message.chat.id,db.read())
                db.close()
            else:
                bot.sendMessage(update.message.chat.id,'No Tiene Permiso')
            return
        # end

        # comandos de usuario
        if '/tuto' in msgText:
            tuto = open('tuto.txt','r')
            bot.sendMessage(update.message.chat.id,tuto.read())
            tuto.close()
            return
        if '/info' in msgText:
            getUser = user_info
            isadmin = jdb.is_admin(username)
            if isadmin:
                statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                bot.sendMessage(update.message.chat.id,statInfo)
            else:
                bot.sendMessage(update.message.chat.id,'🚫 No Tiene Permiso para ver esto')     
            return
        if '/zip' in msgText:
            getUser = user_info
            if getUser:
                try:
                   size = int(str(msgText).split(' ')[1])
                   getUser['zips'] = size
                   jdb.save_data_user(username,getUser)
                   jdb.save()
                   msg = 'A configurado los zips para '+ sizeof_fmt(size*1024*1024)+' cada parte'
                   bot.sendMessage(update.message.chat.id,msg)
                except:
                   bot.sendMessage(update.message.chat.id,'Error en el comando /zips size')
                return
        if '/acc' in msgText:
            try:
                account = str(msgText).split(' ',2)[1].split(',')
                user = account[0]
                passw = account[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_user'] = user
                    getUser['moodle_password'] = passw
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
                
            except:
                bot.sendMessage(update.message.chat.id,'Error en el comando /acc')
            return
        if '/host' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                host = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_host'] = host
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,saveconfig)
            except:
                bot.sendMessage(update.message.chat.id,'Error en el comando /host')
            return
        if '/repo' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                repoid = int(cmd[1])
                getUser = user_info
                if getUser:
                    getUser['moodle_repo_id'] = repoid
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,saveconfig)
            except:
                bot.sendMessage(update.message.chat.id,'Error en el comando /repo')
            return
        if '/uptype' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                type = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['uploadtype'] = type
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,saveconfig)
            except:
                bot.sendMessage(update.message.chat.id,'Error en el comando /uptype (typo de subida (evidence,draft,calendario,calendarioevea))')
            return
        if '/proxy' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                proxy = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['proxy'] = proxy
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,saveconfig)
            except:
                if user_info:
                    user_info['proxy'] = ''
                    statInfo = infos.createStat(username,user_info,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,saveconfig)
            return
        if '/cancel_' in msgText:
            try:
                cmd = str(msgText).split('_',2)
                tid = cmd[1]
                tcancel = bot.threads[tid]
                msg = tcancel.getStore('msg')
                tcancel.store('stop',True)
                time.sleep(3)
                bot.editMessageText(msg,'❌Tarea Cancelada❌')
            except Exception as ex:
                print(str(ex))
            return
        if '/crypt' in msgText:
            proxy_sms = str(msgText).split(' ')[1]
            proxy = S5Crypto.encrypt(f'{proxy_sms}')
            bot.sendMessage(update.message.chat.id, f'Proxy encryptado:\n{proxy}')
            return
        if '/decrypt' in msgText:
            proxy_sms = str(msgText).split(' ')[1]
            proxy_de = S5Crypto.decrypt(f'{proxy_sms}')
            bot.sendMessage(update.message.chat.id, f'Proxy decryptado:\n{proxy_de}')
            return
        
        #end

        message = bot.sendMessage(update.message.chat.id,'🔎Procesando')

        thread.store('msg',message)

        if '/start' in msgText:
            start_msg = ' Bienvenido a Ultra_Fast \n'
            start_msg+= ' Soporte AQUI TU @ \n'
            start_msg+= ' Antes de comenzar vea el /tuto \n'
            start_msg+= " Para ver las subidas disponibles pulse /config \n\n"
            bot.editMessageText(message,start_msg)
        elif '/files' == msgText and user_info['cloudtype']=='moodle':
             proxy = ProxyCloud.parse(user_info['proxy'])
             client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],proxy=proxy)
             loged = client.login()
             if loged:
                 files = client.getEvidences()
                 filesInfo = infos.createFilesMsg(files)
                 bot.editMessageText(message,filesInfo)
                 client.logout()
             else:
                bot.editMessageText(message,'Error y Causas \n1-Revise su Cuenta\n2-Servidor Desabilitado: '+client.path)
        elif '/txt_' in msgText and user_info['cloudtype']=='moodle':
             findex = str(msgText).split('_')[1]
             findex = int(findex)
             proxy = ProxyCloud.parse(user_info['proxy'])
             client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],proxy=proxy)
             loged = client.login()
             if loged:
                 evidences = client.getEvidences()
                 evindex = evidences[findex]
                 txtname = evindex['name']+'.txt'
                 sendTxt(txtname,evindex['files'],update,bot)
                 client.logout()
                 bot.editMessageText(message,'TxT Aqui')
             else:
                bot.editMessageText(message,'Error y Causas \n1-Revise su Cuenta\n2-Servidor Desabilitado: '+client.path)
             pass
        elif '/del_' in msgText and user_info['cloudtype']=='moodle':
            findex = int(str(msgText).split('_')[1])
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],
                                   proxy=proxy)
            loged = client.login()
            if loged:
                evfile = client.getEvidences()[findex]
                client.deleteEvidence(evfile)
                client.logout()
                bot.editMessageText(message,'🗑Archivo Borrado🗑')
            else:
                bot.editMessageText(message,'Error y Causas \n1-Revise su Cuenta\n2-Servidor Desabilitado: '+client.path)
        # elif '/delall' in msgText and user_info['cloudtype']=='moodle':
        #     proxy = ProxyCloud.parse(user_info['proxy'])
        #     client = MoodleClient(user_info['moodle_user'],
        #                           user_info['moodle_password'],
        #                           user_info['moodle_host'],
        #                           user_info['moodle_repo_id'],
        #                           proxy=proxy)
        #     loged = client.login()
        #     if loged:
        #         evfiles = client.getEvidences()
        #         for item in evfiles:
        #         	client.deleteEvidence(item)
        #         client.logout()
        #         bot.editMessageText(message,'🗑Archivos Borrados🗑')
        #     else:
        #         bot.editMessageText(message,'Error y Causas \n1-Revise su Cuenta\n2-Servidor Desabilitado: '+client.path)       
        elif '/download' in msgText:
            obten_name = msgText.split(" ")[1]
            url = msgText.split(" ")[2]
            ddl(update,bot,message,url,obten_name,file_name='',thread=thread,jdb=jdb)
        ###################################################################
       
        elif '/delete_config' in msgText:
            getUser = user_info
            getUser['moodle_host'] = "--"
            getUser['uploadtype'] =  "--"
            getUser['moodle_user'] = "---"
            getUser['moodle_password'] = "---"
            getUser['moodle_repo_id'] = 4
            getUser['zips'] = 100
            getUser['proxy'] = ""
            jdb.save_data_user(username,getUser)
            jdb.save()
            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
            bot.editMessageText(message,"🗑Configuracion Eliminada🗑")
        elif '/delete_prox' in msgText: 
            getUser = user_info
            getUser['proxy'] = ""
            jdb.save_data_user(username,getUser)
            jdb.save()
            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
            bot.editMessageText(message,"🗑Proxy Eliminado🗑")
        ###############################################################
        
        elif '/aulacened' in msgText:
            getUser = user_info
            getUser['moodle_host'] = "https://aulacened.uci.cu/"
            getUser['uploadtype'] =  "draft"
            getUser['moodle_user'] = "---"
            getUser['moodle_password'] = "---"
            getUser['moodle_repo_id'] = 5
            getUser['zips'] = 248
            jdb.save_data_user(username,getUser)
            jdb.save()
            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
            bot.editMessageText(message,"✅Configuracion de Aulacened cargada")
           
        elif '/uclv' in msgText:
            getUser = user_info
            getUser['moodle_host'] = "https://moodle.uclv.edu.cu/"
            getUser['uploadtype'] =  "calendario"
            getUser['moodle_user'] = "--"
            getUser['moodle_password'] = "--"
            getUser['moodle_repo_id'] = 4
            getUser['zips'] = 398
            jdb.save_data_user(username,getUser)
            jdb.save()
            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
            bot.editMessageText(message,"✅Configuracion de Uclv cargada")
        elif '/uvs' in msgText:
            getUser = user_info
            getUser['moodle_host'] = "https://uvs.ucm.cmw.sld.cu/"
            getUser['uploadtype'] =  "draft"
            getUser['moodle_user'] = "--"
            getUser['moodle_password'] = "--"
            getUser['moodle_repo_id'] = 5
            getUser['zips'] = 120
            jdb.save_data_user(username,getUser)
            jdb.save()
            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
            bot.editMessageText(message,"✅Configuracion de Uvs cargada")
        elif '/evea' in msgText:
            getUser = user_info
            getUser['moodle_host'] = "https://evea.uh.cu/"
            getUser['uploadtype'] =  "calendarioevea"
            getUser['moodle_user'] = "--"
            getUser['moodle_password'] = "--"
            getUser['moodle_repo_id'] = 4
            getUser['zips'] = 200
            jdb.save_data_user(username,getUser)
            jdb.save()
            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
            bot.editMessageText(message,"✅Configuracion de Evea cargada")
        
        elif '/cursos' in msgText:
            getUser = user_info
            getUser['moodle_host'] = "https://cursos.uo.edu.cu/"
            getUser['uploadtype'] =  "calendario"
            getUser['moodle_user'] = "---"
            getUser['moodle_password'] = "---"
            getUser['moodle_repo_id'] = 4
            getUser['zips'] = 98
            jdb.save_data_user(username,getUser)
            jdb.save()
            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
            bot.editMessageText(message,"✅Configuracion de Cursos cargada")
        
        elif '/eva' in msgText:
            getUser = user_info
            getUser['moodle_host'] = "https://eva.uo.edu.cu/"
            getUser['uploadtype'] =  "draft"
            getUser['moodle_user'] = "---"
            getUser['moodle_password'] = "---."
            getUser['moodle_repo_id'] = 4
            getUser['zips'] = 98
            jdb.save_data_user(username,getUser)
            jdb.save()
            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
            bot.editMessageText(message,"✅Configuracion de Eva cargada")
        
        elif "/artem" in msgText:
            getUser = user_info
            getUser['moodle_host'] = "http://www.aulavirtual.art.sld.cu/"
            getUser['uploadtype'] =  "calendarioevea"
            getUser['moodle_user'] = ""
            getUser['moodle_password'] = ""
            getUser['moodle_repo_id'] = 5
            getUser['zips'] = 90
            jdb.save_data_user(username,getUser)
            jdb.save()
            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
            bot.editMessageText(message,"✅Configuracion de Aula Artemisa cargada")
            
        elif '/eduvirtual' in msgText:
            getUser = user_info
            getUser['moodle_host'] = "https://eduvirtual.uho.edu.cu/"
            getUser['uploadtype'] =  "blog"
            getUser['moodle_user'] = ""
            getUser['moodle_password'] = ""
            getUser['moodle_repo_id'] = 3
            getUser['zips'] = 8
            jdb.save_data_user(username,getUser)
            jdb.save()
            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
            bot.editMessageText(message,"✅Configuracion de Eduvirtual cargada")
        
        elif "/gtm" in msgText:
            getUser = user_info
            getUser['moodle_host'] = "https://aulauvs.gtm.sld.cu/"
            getUser['uploadtype'] =  "calendarioevea"
            getUser['moodle_user'] = ""
            getUser['moodle_password'] = ""
            getUser['moodle_repo_id'] = 4
            getUser['zips'] = 7
            jdb.save_data_user(username,getUser)
            jdb.save()
            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
            bot.editMessageText(message,"✅Configuracion de Aula Guantanamo cargada")
        ###################################################
        
        elif '/addproxy' in msgText:
            isadmin = jdb.is_admin(username)
            global proxy_list
            
            if isadmin:
                try:
                    proxy = str(msgText).split(' ')[1]
                    proxy_list.append(proxy)
                    zize = len(proxy_list)-1
                    bot.sendMessage(update.message.chat.id,f'Proxy Registrado en la Posicion {zize}')
                except:
                    bot.sendMessage(update.message.chat.id,'❌Error en el comando /addproxy proxy❌')
            else:
                bot.sendMessage(update.message.chat.id,'❌No Tiene Permiso❌')
            return
        elif '/checkproxy' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    msg = 'Proxis Registrados\n'
                    cont = 0
                    for proxy in proxy_list:
                        msg += str(cont) +'--'+proxy+'\n'
                        cont +=1
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,'❌Error en el comando /checkproxy❌')
            else:
                bot.sendMessage(update.message.chat.id,'❌No Tiene Permiso❌')
            return
        elif '/setproxy' in msgText:
            getUser = user_info
            if getUser:
                val = int(str(msgText).split(' ')[1])
                getUser['proxy'] = proxy_list[val]             
                jdb.save_data_user(username,getUser)
                jdb.save()
                statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                bot.editMessageText(message,"✅Proxy cargado")
        
        elif '/config' in msgText:
             msg_nub = "💡LISTA DE NUBES\n"
             msg_nub += "☁️ Eduvirtual ☛ /eduvirtual\n"
             msg_nub += "☁️ Aulacened ☛ /aulacened\n"
             msg_nub += "☁️ Cursos ☛ /cursos\n"
             msg_nub += "☁️ Evea ☛ /evea\n"
             msg_nub += "☁️ Uclv ☛ /uclv\n"
             msg_nub += "☁️ Eva ☛ /eva\n"
             msg_nub += "☁️ Art.sld ☛ /artem\n"   
             bot.editMessageText(message,msg_nub)

        else:
            bot.editMessageText(message,'No entiendo lo q me pides')
    except Exception as ex:
           print(str(ex))
        

def main():
    bot_token = os.environ.get('bot_token')

    #decomentar abajo y modificar solo si se va a poner el token del bot manual
    bot_token = 'AQUI EL TOKEN'

    bot = ObigramClient(bot_token)
    bot.onMessage(onmessage)
    print('Bot Iniciado')
    bot.run()

if __name__ == '__main__':
    try:
        main()
    except:
        main()
