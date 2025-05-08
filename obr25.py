from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import json
import os

# Se você gerou um token.json anteriormente, remova-o para forçar novo consentimento:
if os.path.exists('token.json'):
    os.remove('token.json')

# Escopos necessários (inclui agora 'announcements')
SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses',
    'https://www.googleapis.com/auth/classroom.topics',
    'https://www.googleapis.com/auth/classroom.coursework.me',
    'https://www.googleapis.com/auth/classroom.announcements'
]

# Autenticação OAuth2
flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
creds = flow.run_local_server(port=0)
service = build('classroom', 'v1', credentials=creds)

# Leitura do JSON
with open('Class data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# --- 1) Criar o curso ---
course_data = {
    'name': data['name'],
    'section': data.get('section', ''),
    'descriptionHeading': data.get('name', ''),
    'description': data.get('description', ''),
    'room': data.get('room', ''),
    'ownerId': 'me',
    'courseState': 'PROVISIONED'
}
created_course = service.courses().create(body=course_data).execute()
course_id = created_course['id']
print(f"✅ Curso criado: {created_course['name']} (ID: {course_id})")

# --- 2) Criar tópicos ---
if 'topics' in data:
    for topic in data['topics']:
        topic_body = {'name': topic['name']}
        created_topic = service.courses().topics().create(courseId=course_id, body=topic_body).execute()
        print(f"✅ Tópico criado: {created_topic['name']} (ID: {created_topic['topicId']})")

# --- 3) Criar anúncios (posts) ---
if 'posts' in data:
    for post in data['posts']:
        ann_body = {
            'text': post['announcement']['text'],
            'state': 'PUBLISHED',
            'assigneeMode': post.get('assigneeMode', 'ALL_STUDENTS')
        }
        # Se houver tópico associado no post
        if post.get('topics'):
            # Usamos o nome do primeiro tópico do post
            topic_name = post['topics'][0]['name']
            # Buscar o ID do tópico recém-criado por nome
            resp = service.courses().topics().list(courseId=course_id).execute()
            for t in resp.get('topic', []):
                if t['name'] == topic_name:
                    ann_body['topicId'] = t['topicId']
                    break

        created_ann = service.courses().announcements().create(
            courseId=course_id, body=ann_body).execute()
        print(f"✅ Anúncio criado (ID: {created_ann['id']})")

# --- 4) Criar atividades (courseWork) ---
if 'courseWork' in data:
    for work in data['courseWork']:
        # Monta o corpo da atividade
        coursework_body = {
            'title': work['title'],
            'description': work.get('description', ''),
            'workType': work.get('workType', 'ASSIGNMENT'),
            'state': 'PUBLISHED',
            'maxPoints': work.get('maxPoints'),
        }
        # Adiciona tópico se houver
        if work.get('topic'):
            topic_name = work['topic']['name']
            resp = service.courses().topics().list(courseId=course_id).execute()
            for t in resp.get('topic', []):
                if t['name'] == topic_name:
                    coursework_body['topicId'] = t['topicId']
                    break

        # Datas opcionais
        if 'dueDate' in work:
            coursework_body['dueDate'] = work['dueDate']
        if 'dueTime' in work:
            coursework_body['dueTime'] = work['dueTime']

        created_work = service.courses().courseWork().create(
            courseId=course_id, body=coursework_body).execute()
        print(f"✅ Atividade criada: {created_work['title']} (ID: {created_work['id']})")

# --- 5) Criar anúncios com vídeos de materials no tópico "Videoaulas sBotics" ---
video_topic_id = t.get("Videoaulas sBotics")

if 'materials' in data:
    for material in data['materials']:
        video = material.get('youtubeVideo')
        if video:
            title = video.get('title', 'Vídeo sem título')
            link = video.get('alternateLink', '')

            ann_body = {
                'text': f"{title}\n📺 Assista: {link}",
                'state': 'PUBLISHED',
                'assigneeMode': 'ALL_STUDENTS'
            }

            if video_topic_id:
                ann_body['topicId'] = video_topic_id

            created_video_ann = service.courses().announcements().create(
                courseId=course_id, body=ann_body).execute()
            print(f"📢 Anúncio com vídeo criado: {title}")

print("🎉 Tudo pronto! Curso, tópicos, anúncios e atividades criados.")  
