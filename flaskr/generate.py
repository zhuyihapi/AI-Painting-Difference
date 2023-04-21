# -*- coding: utf-8 -*-
import os
import base64, requests
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from flask import current_app as app
from flaskr.auth import login_required
import replicate
import openai

from flaskr.db import get_db

bp = Blueprint('generate', __name__)


@bp.route('/generate', methods=('GET', 'POST'))
@login_required
def generate():
    # Tokens
    openai.api_key = app.config['OPENAI_KEY']
    replicate_api_token = app.config['REPLICATE_API_TOKEN']
    stability_api_key = app.config['STABILITY_API_KEY']
    os.environ["REPLICATE_API_TOKEN"] = replicate_api_token
    api_host_sdo = os.getenv('API_HOST', 'https://api.stability.ai')
    url_sdo = f"{api_host_sdo}/v1/user/account"

    db = get_db()
    error = None
    user_id = session.get('user_id')

    g.user = get_db().execute(
        'SELECT * FROM user WHERE id = ?', (user_id,)
    ).fetchone()
    credits_current = g.user['credits']

    if request.method == 'POST':
        images = []
        images_dd = []
        images_sd = []
        images_ks2 = []
        prompt = request.form['InputPrompt']

        if request.form.get('SwitchCheckDalle') == 'on':
            n = int(request.form['numberOfPaintingDalle2'])
            size = request.values.get('sizeOfDalle2')
            credits_after = credits_current - n
            if credits_after >= 0:
                res = create_image_dalle2(prompt, n, size)
                credits_current = credits_after
                try:
                    db.execute(
                        "UPDATE user SET credits=? WHERE username=?",
                        (credits_current, g.user['username']),
                    )
                    db.commit()
                except db.IntegrityError:
                    error = "credits update error for dalle2"
                if len(res) > 0:
                    for img in res:
                        images.append(img['url'])
            else:
                error = "Insufficient credits!"

            if error is not None:
                flash(error)

        if request.form.get('SwitchCheckSD') == 'on':
            n = int(request.form['numberOfPaintingSD'])
            size = request.values.get('sizeOfSD')
            steps = int(request.form['num_inference_steps_sd'])
            guidance_scale_sd = float(request.form['guidance_scale_sd'])
            negative_prompt_sd = request.form['negative_prompt_sd']
            credits_after = credits_current - n
            if credits_after >= 0:
                images_sd = create_image_sd(prompt, n, size, steps, guidance_scale_sd, negative_prompt_sd)
                credits_current = credits_after
                try:
                    db.execute(
                        "UPDATE user SET credits=? WHERE username=?",
                        (credits_current, g.user['username']),
                    )
                    db.commit()
                except db.IntegrityError:
                    error = "credits update error for SD"

            else:
                error = "Insufficient credits!"

        if request.form.get('SwitchCheckKS2') == 'on':
            width = int(request.form['widthOfKS2'])
            height = int(request.form['heightOfKS2'])
            steps = int(request.form['stepsOfKS2'])
            credits_after = credits_current - 1
            if credits_after >= 0:
                images_ks2 = create_image_ks2(prompt, width, height, steps)
                credits_current = credits_after
                try:
                    db.execute(
                        "UPDATE user SET credits=? WHERE username=?",
                        (credits_current, g.user['username']),
                    )
                    db.commit()
                except db.IntegrityError:
                    error = "credits update error for SK2"

            else:
                error = "Insufficient credits!"

        if request.form.get('SwitchCheckDD') == 'on':
            credits_after = credits_current - 3
            if credits_after >= 0:
                images_dd.append(create_image_dd(prompt))
                credits_current = credits_after
                try:
                    db.execute(
                        "UPDATE user SET credits=? WHERE username=?",
                        (credits_current, g.user['username']),
                    )
                    db.commit()
                except db.IntegrityError:
                    error = "credits update error for DD"

            else:
                error = "Insufficient credits!"

        # if request.form.get('SwitchCheckSDO') == 'on':
        #
        #     n = int(request.form['numberOfPaintingSD'])
        #     size = request.values.get('sizeOfSD')
        #     steps = int(request.form['stepsOfSD'])
        #     credits_after = credits_current - n
        #     if credits_after >= 0:
        #         images_sd = create_image_sd(prompt, n, size, steps)
        #         credits_current = credits_after
        #         try:
        #             db.execute(
        #                 "UPDATE user SET credits=? WHERE username=?",
        #                 (credits_current, g.user['username']),
        #             )
        #             db.commit()
        #         except db.IntegrityError:
        #             error = "credits update error for SD"
        #
        #     else:
        #         error = "Insufficient credits!"

    g.user = get_db().execute(
        'SELECT * FROM user WHERE id = ?', (user_id,)
    ).fetchone()

    return render_template('generate.html', **locals())


def create_image_dalle2(prompt, n, size):
    response = []
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=n,
            size=size,
        )
    except openai.error.OpenAIError as e:
        # print(e.http_status)
        # print(e.error)
        flash('DALL E 2 returns an error! ' + e.error['message'], 'error')
        response = []
        return response
    return response['data']


def create_image_sd(prompt, num_outputs, image_dimensions, num_inference_steps, guidance_scale, negative_prompt):
    output = replicate.run(
        "stability-ai/stable-diffusion:db21e45d3f7023abc2a46ee38a23973f6dce16bb082a930b0c49861f96d1e5bf",
        input={"prompt": prompt,
               "num_outputs": num_outputs,
               "image_dimensions": image_dimensions,
               "num_inference_steps": num_inference_steps,
               "guidance_scale": guidance_scale,
               "negative_prompt": negative_prompt
               })

    return output


def create_image_ks2(prompt, width, height, num_inference_steps):
    # red cat, 4k photo
    output = replicate.run(
        "ai-forever/kandinsky-2:601eea49d49003e6ea75a11527209c4f510a93e2112c969d548fbb45b9c4f19f",
        input={"prompt": prompt,
               "width": width,
               "height": height,
               "num_inference_steps": num_inference_steps
               }
    )
    return output


def create_image_dd(prompt):
    output = replicate.run(
        "nightmareai/disco-diffusion:3c128f652e9f24e72896ac0b019e47facfd6bccf93104d50f09f1f2196325507",
        input={"steps": 100,
               "prompt": prompt,
               "width": 514,
               "height": 384,
               "diffusion_model": "512x512_diffusion_uncond_finetune_008100"
               }
    )

    response = []
    # for image in output:
    #     display(image)

    # The nightmareai/disco-diffusion model can stream output as it's running.
    # The predict method returns an iterator, and you can iterate over that output.
    for url_dd in output:
        # https://replicate.com/nightmareai/disco-diffusion/versions/3c128f652e9f24e72896ac0b019e47facfd6bccf93104d50f09f1f2196325507/api#output-schema
        # print(item)
        response.append(url_dd)
    # print(response)
    return response[-1]

# @bp.before_app_request
# def load_logged_in_user():
#     user_id = session.get('user_id')
#
#     if user_id is None:
#         g.user = None
#     else:
#         g.user = get_db().execute(
#             'SELECT * FROM user WHERE id = ?', (user_id,)
#         ).fetchone()

# def create_image_sdo(prompt):
#     # A lighthouse on a cliff
#     engine_id = "stable-diffusion-v1-5"
#     api_host = os.getenv('API_HOST', 'https://api.stability.ai')
#     api_key = app.config['STABILITY_API_KEY']
#     response = requests.post(
#         f"{api_host}/v1/generation/{engine_id}/text-to-image",
#         headers={
#             "Content-Type": "application/json",
#             "Accept": "application/json",
#             "Authorization": f"Bearer {api_key}"
#         },
#         json={
#             "text_prompts": [
#                 {
#                     "text": prompt
#                 }
#             ],
#             "cfg_scale": 7,
#             "clip_guidance_preset": "FAST_BLUE",
#             "height": 512,
#             "width": 512,
#             "samples": 1,
#             "steps": 30,
#         },
#     )
#
#     if response.status_code != 200:
#         raise Exception("Non-200 response: " + str(response.text))
#
#     data = response.json()
#
#     for i, image in enumerate(data["artifacts"]):
#         with open(f"./out/v1_txt2img_{i}.png", "wb") as f:
#             f.write(base64.b64decode(image["base64"]))
#     return
