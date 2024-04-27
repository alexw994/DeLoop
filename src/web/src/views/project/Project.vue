<template>
    <div>
        <div v-if="!empty">
            <div v-if="hasProject">
                <div class="w-full flex justify-center">
                    <div class="flex flex-col w-full h-full px-[1rem] py-[1rem] space-y-[1rem]">
                        <el-breadcrumb separator="/">
                            <el-breadcrumb-item :to="{ path: '/' }">Home</el-breadcrumb-item>
                            <el-breadcrumb-item> Projects</el-breadcrumb-item>
                        </el-breadcrumb>
                        <el-card class="w-full h-max">

                            <div class="flex justify-between space-x-[2rem]">
                                <el-input v-model="search" placeholder="Type to search">
                                    <template #prefix>
                                        <el-icon>
                                            <Search />
                                        </el-icon>
                                    </template>
                                </el-input>
                                <el-button color="#092B2C" style="color: white"><router-link to="/projects/new">Create a
                                        New
                                        Project</router-link></el-button>
                            </div>
                        </el-card>
                        <el-row>
                            <el-col v-for="(project, index) in projects" :key="project.name" :span="5"
                                :offset="index > 0 ? 1 : 0">
                                <el-card :body-style="{ padding: '2px' }">
                                    <img :src="project.coverUrl" class="image"
                                        @click.native="showProjectRecords(index)" />
                                    <el-descriptions :title=project.name
                                        style="display: flex; justify-content: space-between; padding: 10px; align-items: center;">
                                        <el-descriptions-item>
                                            <el-popover placement="right" :width="80" trigger="click">

                                                <template #reference>
                                                    <el-button
                                                        style="margin-right: 16px; border: 0px; transform: rotate(90deg)"
                                                        :icon="More"></el-button>
                                                </template>
                                                <el-row>
                                                    <el-button style="margin-right: 16px;" size="small" type="success"
                                                        text @click="dialogEditBackendFormVisible = true"> Edit </el-button>
                                                </el-row>

                                                <el-row>
                                                    <el-button style="margin-right: 16px;" size="small" type="danger"
                                                        text @click="deleteProject"> Delete </el-button>
                                                </el-row>

                                                <el-dialog v-model="dialogEditBackendFormVisible"
                                                    style="max-width: 500px;" align-center>

                                                    <template #header="{ }">
                                                        <div class="form-header" style="font-size: small">
                                                            <h4>Project </h4>

                                                        </div>

                                                    </template>

                                                    <el-form label-width="auto"
                                                        style="max-width: 500px ; margin-top: -20px; margin-bottom: 20px;">
                                                        <el-form-item label="Name" size="small">
                                                            <el-input v-model="project.name" autocomplete="off"
                                                                disabled />
                                                        </el-form-item>
                                                        <el-form-item label="Infer Model" size="small">
                                                            <el-input v-model="project.infer_model" autocomplete="off"
                                                                disabled />
                                                        </el-form-item>
                                                        <el-form-item label="Method" size="small">
                                                            <el-input v-model="project.method" autocomplete="off" />
                                                        </el-form-item>
                                                        <el-form-item label="Batch" size="small">
                                                            <el-input v-model="project.batch" autocomplete="off" />
                                                        </el-form-item>
                                                        <el-form-item label="Interval" size="small">
                                                            <el-input v-model="project.time_interval"
                                                                autocomplete="off">
                                                                <template #suffix>
                                                                    <span>Minutes</span>
                                                                </template>
                                                            </el-input>
                                                        </el-form-item>

                                                        <el-divider content-position="left"></el-divider>

                                                        <el-form-item label="AL Backend API" size="small">
                                                            <el-input v-model="project.al_backend_config.api"
                                                                autocomplete="off" />
                                                        </el-form-item>
                                                        <el-form-item label="AL Backend Headers" size="small">
                                                            <el-input v-model="project.al_backend_config.hearders"
                                                                autocomplete="off" :rows="2" type="textarea" />
                                                        </el-form-item>
                                                        <el-button style="float:right; margin-top:-5px" size="small"
                                                            type="success" text @click="saveProjectConfig(project, {
            api: project.al_backend_config.api,
            headers: project.al_backend_config.headers
        })">
                                                            Confirm</el-button>
                                                    </el-form>
                                                </el-dialog>

                                            </el-popover>
                                        </el-descriptions-item>
                                    </el-descriptions>
                                    <el-descriptions style="margin-top: -20px;">
                                        <el-descriptions-item>
                                            <el-row style="padding: 10px; top: -10px">
                                                <el-col>
                                                    module: {{ project.infer_model }}
                                                </el-col>
                                                <el-col>
                                                    dataset records: {{ project.record_count }}
                                                </el-col>
                                            </el-row>
                                            <el-row style="padding-left: 8px; top: -10px">
                                                <el-tag size="small" color="#F7AC67"
                                                    style="color: white; border: 0cap;">
                                                    {{ project.type }}</el-tag>
                                                <div v-if="project.has_al_backend && project.al_backend_avaliable">
                                                    <el-tag size="small" type="primary"
                                                        style="margin-left: 5px; border: 0cap;">
                                                        Backend</el-tag>
                                                </div>
                                                <div v-else>
                                                    <el-tag size="small" type="error"
                                                        style="margin-left: 5px; border: 0cap;">
                                                        No Backend</el-tag>
                                                </div>
                                            </el-row>
                                            <div style="display: flex; flex-wrap:  wrap;">
                                            <div v-for="(version, index) in project.archived_version" :key="version">
                                                <el-tag size="small" type="primary"
                                                    style="margin-left: 5px; border: 0cap;">
                                                    {{ version.split('_')[4] }}
                                                </el-tag>
                                            </div>
                                            </div>

                                        </el-descriptions-item>
                                    </el-descriptions>
                                </el-card>
                            </el-col>
                        </el-row>
                    </div>
                </div>

            </div>

            <div v-else>
                <div class="flex my-[4rem]">
                    <img src="@/assets/design-and-development-process.svg" class="w-2/5 mx-auto">
                </div>

                <div class="col-12 flex justify-center items-center">
                    <div class="text-content font-sans text-left max-w-[460px]">
                        <h1 class="text-xl">Create a new project to collect data records produced in the production
                            environment.
                        </h1>
                        <div class="pt-4"></div>
                        <h4>This project can configure an active learning backend and image collector to select records
                            more
                            efficiently.</h4>

                        <div class="pt-4"></div>

                        <div class="col-12 flex justify-center items-center">
                            <el-button color="#092B2C" style="color: white"><router-link to="/projects/new">Create a New
                                    Project

                                </router-link></el-button>
                        </div>

                    </div>
                </div>

            </div>
        </div>
    </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue';
import { useRouter } from 'vue-router'
import { Edit, Api, Delete, More } from '@icon-park/vue-next';
import request from '@/axios';
import { ElMessage } from "element-plus";

const router = useRouter();

const empty = ref(true)
const hasProject = computed(() => projects.value.length > 0)

const search = ref('');
const filter = computed(() =>
    projects.value.filter(
        (project) =>
            !search.value ||
            project.name.toLowerCase().includes(search.value.toLowerCase())
    )
)

const dialogEditBackendFormVisible = ref(false);
const projects = ref([]);
const form = ref({
    api: undefined,
    headers: undefined
});




const stringify = (headers) => {
    const str = JSON.stringify(headers)
    if (str.length < 20) return str
    return str.slice(0, 20) + '...'
}

const saveProjectConfig = (project, form) => {
    var project_name = project.name
    var image_url = project.coverUrl
    var time_interval = project.time_interval
    var batch = project.batch

    request.put(`/api/v1/de/projects`, { 'project_name': project_name, "al_backend_config": {"api": form.api, "headers": form.headers},'batch': batch, 'time_interval': time_interval}).then(
        request.post(`/api/v1/de/al_backend/health`, { 'project_name': project_name, 'image_url': image_url }).then((response) => {
            dialogEditBackendFormVisible.value = false
            project.has_al_backend = true
            project.al_backend_config = { api: form.api, headers: form.headers, referer: 'page' }
            project.al_backend_avaliable = true
        }).catch((error) => {
            ElMessage.error(project_name + 'Backend is unavailable')
            project.has_al_backend = true
            project.al_backend_config = { api: form.api, headers: form.headers, referer: 'page' }
            project.al_backend_avaliable = false
            dialogEditBackendFormVisible.value = false
        })
    ).catch((error) => {
        ElMessage.error(project_name + 'Config upload failure')
        project.al_backend_avaliable = false
        project.has_al_backend = false
        project.al_backend_config = undefined
        dialogEditBackendFormVisible.value = false
        return false, false
    })
}

const deleteProject = (row) => {
    request.delete(`/api/v1/de/projects/${row.name}`).then(
        projects.value = projects.value.filter(project => project.name !== row.name)
    )
}


const showProjectRecords = (index) => {
    router.push(`/data?project_name=${projects.value[index].name}`)
}

const checkALBackendHealth = (project) => {
    var project_name = project.name
    var image_url = project.coverUrl

    request.post(`/api/v1/de/al_backend/health`, { "project_name": project_name, "image_url": image_url }).then((response) => {
        project.al_backend_avaliable = true
    }).catch((error) => {
        ElMessage.error(project_name + "Backend is unavaliable")
        project.al_backend_avaliable = false
    })
}

onMounted(
    () => {
        request.get("/api/v1/de/projects").then((response) => {
            projects.value = response.data;
            empty.value = false
            // 封面

            for (var project of projects.value) {
                if (!project.has_al_backend){
                    project.al_backend_config = {api: undefined, headers: '{}'}

                }
                request.get(`/api/v1/de/records?project_name=${project.name}&size=1`).then((response) => {
                    var tmp = response.data[0]
                    project.coverUrl = tmp.image_shared_url

                    if (project.has_al_backend) {
                        checkALBackendHealth(project)
                    }

                })

                // dataset info
                request.get(`/api/v1/de/datasets?project_name=${project.name}&archived=0`).then((response) => {
                    project.record_count = response.data[0].count
                })

                request.get(`/api/v1/de/datasets?project_name=${project.name}&archived=1`).then((response) => {
                    project.archived_version = []
                    for (var d of response.data)
                    {
                        project.archived_version.push(d.name)
                    }
                    console.log(project.archived_version)
                })

                console.log(project)
            }
        })
    }
)


</script>


<style>
.time {
    font-size: 12px;
    color: #999;
}

.image {
    width: 100%;
    display: block;
}
</style>