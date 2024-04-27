<template>
  <div>
    <div class="w-full flex justify-center">
      <div class="flex flex-col w-full h-full px-[1rem] py-[1rem] space-y-[1rem]">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/' }">Home</el-breadcrumb-item>
          <el-breadcrumb-item> Datasets</el-breadcrumb-item>
        </el-breadcrumb>
        <el-card class="w-full h-max">

          <template #header>
            <div class="flex w-full items-center">
              <OpenOne class="ml-[1rem]" theme="filled" size="42" fill="#94A3B8"/>
              <span class="m-[0.6rem] text-2xl font-600">Unarchived Datasets</span>
            </div>
          </template>

          <el-table :data="unarchived" :height="cardHeight.value * 1.7 + `px`" class="w-full max-h-full">
            <el-table-column prop="project_name" label="Project" min-width="100px"/>
            <el-table-column prop="count" label="Count" min-width="40px"/>
            <el-table-column prop="initialization" label="INIT" min-width="40px"/>
            <el-table-column prop="pending_oracle_annotation" label="ORA" min-width="40px"/>
            <el-table-column prop="auto_annotation_completed" label="AUTO" min-width="40px"/>
            <el-table-column prop="human_annotation_completed" label="HUMAN" min-width="40px"/>
            <el-table-column prop="invalid" label="INVALID" min-width="40px"/>

            <el-table-column label="Operation" min-width="0px">

              <template #default="scope">
                <el-button size="small" color="#092B2C" style="color: white" @click="labelingDataset()"
                           :icon="Edit"/>
                <el-button size="small" color="#092B2C" style="color: white"
                           @click="archiveDataset(scope.row.project_name)" :icon="Save"/>
              </template>
            </el-table-column>

          </el-table>
        </el-card>

        <el-card class="w-full h-max">

          <template #header>
            <div class="flex w-full items-center">
              <Okay class="ml-[1rem]" theme="filled" size="42" fill="#94A3B8"/>
              <span class="m-[0.6rem] text-2xl font-600">Archived Datasets</span>
            </div>
          </template>

          <el-table :data="archived" :height="cardHeight.value * 1.3+`px`" class="w-full max-h-full">
            <el-table-column prop="name" label="Name" min-width="140px"/>
            <el-table-column prop="project_name" label="Project" min-width="40px"/>
            <el-table-column prop="count" label="Count" min-width="40px"/>
            <!--            <el-table-column prop="initialization" label="INIT" min-width="40px"/>-->
            <!--            <el-table-column prop="pending_oracle_annotation" label="ORA" min-width="40px"/>-->
            <el-table-column prop="auto_annotation_completed" label="AUTO" min-width="40px"/>
            <el-table-column prop="human_annotation_completed" label="HUMAN" min-width="40px"/>
            <!--            <el-table-column prop="invalid" label="INVALID" min-width="40px"/>-->

            <el-table-column label="Operation" min-width="0px">

              <template #default="scope">
                <el-button size="small" type="danger" @click="deleteDataset(scope.row.name)" :icon="Delete"/>
                <!--                <el-button size="small" color="#092B2C" style="color: white"-->
                <!--                           @click="UploadDatasetToHF(scope.row.name)" :icon="Upload"/>-->
                <el-button size="small" color="#092B2C" style="color: white"
                           @click="DownloadDataset(scope.row.name, 'hf')" :icon="Download"> hf
                </el-button>
                <el-button size="small" color="#092B2C" style="color: white"
                           @click="DownloadDataset(scope.row.name, 'raw')" :icon="Download"> raw
                </el-button>
              </template>
            </el-table-column>

          </el-table>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import {computed, ref, onMounted} from 'vue';
import {useRouter} from 'vue-router'
import {Edit, Save, Upload, Api, Delete, Peoples, Search, Download, Okay, OpenOne} from '@icon-park/vue-next';
import request from '@/axios';
import {ElMessage, ElSubMenu} from "element-plus";

const router = useRouter();

const archived = ref([]);
const unarchived = ref([]);
const cardHeight = ref(1);

const labelingDataset = () => {
  router.push(`/labeling`)
}


const archiveDataset = (project_name) => {
  request.post("/api/v1/de/datasets/archive", {'project_name': project_name}, {timeout: 5000}).then((response) => {
    ElMessage.success('Archived Susscess')
    request.get(`/api/v1/de/datasets?archived=1`).then((response) => {
      archived.value = response.data;
      console.log(archived.value)
    })
  })
  router.push("/datasets")
}

const DownloadDataset = (archived_dataset_name, format) => {
  request.post("/api/v1/de/datasets/download", {
    'archived_dataset_name': archived_dataset_name,
    'format': format
  }, {timeout: 5000}).then((response) => {

    console.log(response.data)
    var fileUrl = response.data
    var fileName = archived_dataset_name + '_' + format + '.zip'

    const link = document.createElement('a');
    link.href = fileUrl;
    link.download = fileName;

    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);
  })
  router.push("/datasets")
}

const UploadDatasetToHF = (archived_dataset_name, hf_token, space) => {
  console.log(archived_dataset_name)
  request.post(`/api/v1/de/datasets/uploadhf`, {
    'archived_dataset_name': archived_dataset_name,
    "hf_token": hf_token,
    "space": space
  }, {timeout: 5000}).then((response) => {
    archived.value = response.data;
    ElMessage.success('Upload to huggingface success')

    console.log(archived.value)
  }).catch((error) => {
    ElMessage.error('Upload to huggingface failure')
  })
  router.push("/datasets")
}


const deleteDataset = (archived_dataset_name) => {
  console.log(archived)
  request.delete(`/api/v1/de/datasets/${archived_dataset_name}`).then(
      archived.value = archived.value.filter(d => d.name !== archived_dataset_name)
  )
}

onMounted(
    () => {
      cardHeight.value = ((window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight)) / 2

      request.get(`/api/v1/de/datasets?archived=1`).then((response) => {
        archived.value = response.data;
        console.log(archived.value)
      })
      request.get(`/api/v1/de/datasets?archived=0`).then((response) => {
        unarchived.value = response.data;
        console.log(unarchived.value)

      })
    }
)


</script>
