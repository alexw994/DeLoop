<template>
    <div class="w-full flex justify-center">
        <div class="flex flex-col h-full w-full px-[1rem] py-[1rem] space-y-[1rem]">

            <el-card class="w-full h-max">
                <div class="h-full w-full flex">
                    <div class="flex-col w-4/5 m-auto justify-center text-center">
                        <h1 class="text-xl">New Project</h1>
                        <el-divider content-position="left"></el-divider>

                        <el-form ref="createProjectRef" :model="project" label-width="80px">
                            <el-form-item label="Name: ">
                                <el-input v-model="project.name" placeholder="Name"></el-input>
                            </el-form-item>
                            <!-- TODO 从record中选择现有的Module -->

                            <el-form-item label="Describle:" size="large">
                                <el-input v-model="project.describle" placeholder="..." :rows="3"
                                    type="textarea"></el-input>
                            </el-form-item>


                            <el-form-item label="Type">
                                <el-select v-model="project.type" placeholder="Defualt ObjectDetection">
                                    <el-option v-for="item in typeSelect" :key="item.value" :label="item.label"
                                        :value="item.value">
                                    </el-option>
                                </el-select>
                            </el-form-item>
                            <el-divider content-position="left"></el-divider>

                            <el-form-item label="Method">
                                <el-select v-model="project.method" placeholder="Defualt FN">
                                    <el-option v-for="item in methodSelect" :key="item.value" :label="item.label"
                                        :value="item.value">
                                    </el-option>
                                </el-select>
                            </el-form-item>

                            <el-form-item label="Batch">
                                <el-input v-model="project.batch" placeholder="batch"></el-input>
                            </el-form-item>

                            <el-form-item label="Interval: ">
                                <el-input v-model="project.time_interval" placeholder="1">
                                    <template #suffix>
                                        <span>Hours</span>
                                    </template>
                                </el-input>
                            </el-form-item>

                            <el-divider content-position="left"></el-divider>

                            <el-form-item label="Backend">
                                <el-switch v-model="project.has_al_backend" style="--el-switch-on-color: #092B2C" />
                            </el-form-item>


                            <div v-if="project.has_al_backend">

                                <el-form-item label="POST API: ">
                                    <el-input v-model="project.al_backend_config.api"
                                        placeholder="http://dev-env-host:port/api/v1/dummy"></el-input>
                                </el-form-item>

                                <el-form-item label="Header: ">
                                    <el-input v-model="project.al_backend_config.headers"
                                        placeholder="{key1:value1, key2:value2}" :rows="3" type="textarea"></el-input>
                                </el-form-item>


                            </div>


                            <div style="display: flex; justify-content: center;">
                                <el-card class="w-100">
                                    <div style="text-align: left;">
                                        <el-row>
                                            <el-text size="large">
                                                Install Deloop to upload data to the project or configure project
                                                information during the initial
                                                upload, enabling automatic creation.
                                            </el-text>
                                        </el-row>
                                        <el-row>Install deloop:
                                            <el-row>
                                                <code style="color: #092B2C;">
                        pip install deloop
                    </code>
                                            </el-row>
                                        </el-row>
                                        <el-row>
                                        </el-row>
                                        <el-row>
                                            <el-text size="large">
                                                Use <code style="color: #092B2C;"> deloop.create_project(...) </code>
                                                before <code style="color: #092B2C;"> deloop.upload_image(...) </code>
                                                and <code style="color: #092B2C;">deloop.upload_record(...)</code>
                                            </el-text>
                                        </el-row>
                                    </div>
                                </el-card>
                            </div>

                        </el-form>
                    </div>
                </div>
                <!-- <div class="h-full w-full flex">

                    <div class="flex-row w-5/6 m-auto justify-center">
                        <el-card header="Python Script">
                            <CodeEditor height="80vh" width="63vw" font-size="14px" :languages="[['python', 'Python']]"
                                :tab-spaces="4" :value="module.script"></CodeEditor>
                        </el-card>
                    </div>
                </div> -->

                <div class="pt-4"></div>
                <div class="flex-col w-4/5 m-auto justify-center text-center">
                    <el-button color="#092B2C" style="color: white" @click="onClickSave">Create</el-button>
                    <el-button><router-link to="/projects">Cancel</router-link></el-button>
                </div>
            </el-card>
        </div>
    </div>
</template>

<script setup>

import { ElMessage } from "element-plus";
import { computed, ref, unref, onMounted } from 'vue';
import hljs from 'highlight.js';
import CodeEditor from 'simple-code-editor';
import request from '@/axios';

import { useRouter } from 'vue-router'
const router = useRouter();

const createProjectRef = ref();

const methodSelect = ref([{ label: 'FN', value: 'FN' }])

const project = ref({
    name: undefined,
    type: undefined,
    describle: '',
    method: 'FN',
    has_al_backend: false,
    time_interval: 60,
    batch: 50,
    al_backend_config: {
        api: undefined,
        headers: '{}'
    }
});

const onClickSave = () => {
    const form = unref(createProjectRef)
    if (!form) {
        ElMessage.warning('Form Invalid')
        return
    }

    if (project.value.name == undefined) {
        ElMessage.warning('Form Invalid')
        return
    }

    if (project.value.method == undefined) {
        ElMessage.warning('Form Invalid')
        return
    }

    if (project.value.batch == undefined) {
        ElMessage.warning('Form Invalid')
        return
    }

    if (project.value.time_interval == undefined) {
        ElMessage.warning('Form Invalid')
        return
    }


    if (project.value.has_al_backend) {
        if (project.value.al_backend_config.api == undefined) {
            ElMessage.warning('Form Invalid')
            return
        }

        if (project.value.al_backend_config.headerst == undefined) {
            ElMessage.warning('Form Invalid')
            return
        }
    }


    request.post("/api/v1/de/projects", project.value)
        .then((response) => {
            ElMessage.success("Successful")
        })
}

</script>
