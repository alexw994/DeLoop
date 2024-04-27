<template>
  <div>
    <div class="w-full flex justify-center">
      <div class="flex flex-col w-full h-full px-[1rem] py-[1rem] space-y-[1rem]">
        <el-card class="w-full h-full">
          <iframe :src="lsUrl" id="label-studio" style="width: 100%; border: none; top:0;left:0"
                  :height="iframeHeight + `px`">
          </iframe>
        </el-card>
        <!-- 标注 -->

      </div>
    </div>
  </div>
</template>

<script setup>
import {computed, ref, onMounted} from 'vue';
import {useRouter} from 'vue-router'
import {Edit, Save, Api, Delete, Peoples, Search, CloseOne, OpenOne} from '@icon-park/vue-next';
import request from '@/axios';
import axios from "axios"
import {ElMessage} from "element-plus";
import LabelStudio from 'label-studio';
import 'label-studio/build/static/css/main.css';
import Cookies from 'js-cookie';
import {isReactive} from 'vue';

const lsUrl = ref('')
const iframeHeight = ref()

onMounted(
    () => {
      const iframe = document.getElementById('label-studio');

      console.log(lsUrl.value)
      // 只加载一次Label Studio
      request.get("/api/v1/de/ls_auth").then((response) => {
        var url = response.data.url
        const formData = new URLSearchParams();
        formData.append('csrfmiddlewaretoken', response.data.data.csrfmiddlewaretoken);
        formData.append('email', response.data.data.email);
        formData.append('password', response.data.data.password);
        formData.append('persist_session', 'on');

        var headers = response.data.headers
        var cookie = response.data.cookie

        Cookies.set('csrftoken', response.data.cookie.csrftoken)
        Cookies.set('sessionid', response.data.cookie.sessionid)

        headers['Content-Type'] = "application/x-www-form-urlencoded"
        // headers['Upgrade-Insecure-Requests'] = 1

        console.log(cookie)
        console.log(document.cookie)

        iframeHeight.value = (window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight) * 0.85

        console.log(url)
        request.post('/user/login', formData, {headers: headers}).then((response) => {
          request.put("/api/v1/de/apply_ls_project", {}, {timeout: 5000}).then((response) => {
            console.log(response.data)
            lsUrl.value = "/"
          })
        })
      })
    }
)


const onLabelStudioLoad = function (LS) {
  var c = LS.annotationStore.addAnnotation({
    userGenerate: true
  });
  LS.annotationStore.selectAnnotation(c.id);
}


const onSubmitAnnotation = function (LS, annotation) {
  console.log(annotation.serializeAnnotation())
}

</script>