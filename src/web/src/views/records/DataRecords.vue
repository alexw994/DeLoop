<template>
    <div class="w-full justify-center">
        <el-dialog v-model="showUpdate" top="5vh" width="98%" title="View Yaml">
            <CodeEditor height="60vh" :value="obj2yaml(updatedPod)" readOnly></CodeEditor>
        </el-dialog>

        <el-dialog v-model="showLog" top="5vh" width="98%" title="View Log">
            <CodeEditor height="60vh" :value="logs" mode="log" readOnly light></CodeEditor>
        </el-dialog>

        <div class="flex flex-col w-full h-full px-[1rem] py-[1rem] space-y-[1rem]">
            <el-breadcrumb separator="/">
                <el-breadcrumb-item :to="{ path: '/' }">Home</el-breadcrumb-item>
                <div v-if="project_name">
                    <el-breadcrumb-item> Data Records</el-breadcrumb-item>
                    <el-breadcrumb-item> {{ project_name }}</el-breadcrumb-item>
                </div>

                <div v-else>
                    <el-breadcrumb-item> Data Records</el-breadcrumb-item>
                </div>
            </el-breadcrumb>

            <el-card class="h-max flex-row">
                <template #header>
                    <div class="flex w-full space-x-[2rem]">
                        <el-input v-model="search" placeholder="Type to search">
                            <template #prefix>
                                <el-icon>
                                    <Search />
                                </el-icon>
                            </template>
                        </el-input>
                    </div>
                </template>
                <el-table :data="filter" v-loading="loading" v-el-table-infinite-scroll="load"
                    :infinite-scroll-disabled="disabled" :height="tableHeight + `px`" class="w-full max-h-full"
                    @row-click="openImageDialog">
                    <el-table-column type="index" width="50" index="indexInit" />
                    <el-table-column prop="record_id" label="Id" min-width="0px" show-overflow-tooltip="false" />
                    <el-table-column prop="image_shared_url" label="Image" min-width="50px">
                        <template v-slot="{ row }">
                            <img ref="imageRef" :src="row.image_shared_url" alt="Thumbnail"
                                style="max-width: 50px; max-height: 50px;">
                        </template>
                    </el-table-column>
                    <el-table-column prop="state" label="State" min-width="100px">
                        <template #header>
                            <el-select v-model="filterState" placeholder="State">
                                <el-option v-for="filter in statusFilters" :key="filter.value" :label="filter.label"
                                    :value="filter.value"></el-option>
                            </el-select>
                        </template>
                    </el-table-column>

                    <el-table-column prop="project_name" label="Project" min-width="100px">
                        <template #header>
                            <el-input v-model="router.currentRoute.value.query.project_name" placeholder="Project">
                            </el-input>
                        </template>
                    </el-table-column>

                    <el-table-column prop="timestamp" label="Timestamp" sortable min-width="120px" />
                    <el-table-column prop="bboxes" label="Bboxes" min-width="60px" show-overflow-tooltip="false">
                        <template v-slot="{ row }">
                            <div v-html="stringify(row.bboxes)"></div>
                        </template>
                    </el-table-column>
                    <el-table-column prop="uncertainty" label="Uncertainty" sortable min-width="90px"
                        :formatter="formatUncertainty" />
                    <el-table-column label="Operation" min-width="80px">
                        <template #default="scope">
                            <el-button size="small" type="danger" @click="reocordDelete(scope.row)" :icon="Delete"
                                circle class="wl-[1rem]" />
                        </template>
                    </el-table-column>
                </el-table>
            </el-card>
            <el-dialog v-model="dialogVisible" @opened="onDialogOpened" destroy-on-close="true" :width="dialogWidth">
                <template #header="{ close, titleId, titleClass }">
                    <div class="my-header">
                        <h4 :id="titleId" :class="titleClass" :style="{ fontWeight: 'bold' }"> Details</h4>
                    </div>
                </template>
                <canvas ref="canvasRef"></canvas>
            </el-dialog>

        </div>
    </div>
</template>


<style>
body {
    margin: 0;
}

.example-showcase .el-loading-mask {
    z-index: 9;
}
</style>


<style scoped>
.my-header {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
}
</style>

<script setup>

import {
    FileDisplayOne, Delete, CubeThree, Search, Terminal, Log
} from '@icon-park/vue-next';
import { ref, unref, onMounted, watchEffect, computed } from 'vue';
import CodeEditor from '@/components/CodeEditor.vue';
import request from '@/axios';
import { useRouter } from 'vue-router'
import { default as vElTableInfiniteScroll } from "el-table-infinite-scroll";

const router = useRouter();
const showUpdate = ref(false);

const updatedPod = ref({});

const recordData = ref([])
const showTableRecordData = ref([])

const disabled = ref(false)
const page = ref(0);
const total = ref(20);

const dialogVisible = ref(false)
const dialogWidth = ref(false)
const selectedRecord = ref({});
const canvasRef = ref(null);
const tableHeight = ref();

const load = () => {
    if (recordData.value.length === 0) {
        request.get("/api/v1/de/records").then((response) => {
            recordData.value = response.data;
            total.value = recordData.value.length
            loading.value = false

            if (disabled.value) return;

            page.value++;

            if (page.value <= total.value) {
                showTableRecordData.value = showTableRecordData.value.concat(recordData.value[page.value]);
            }

            if (page.value === total.value) {
                disabled.value = true;
            }

        })

    }
    else {

        if (disabled.value) return;

        page.value++;

        if (page.value <= total.value) {
            showTableRecordData.value = showTableRecordData.value.concat(recordData.value[page.value]);
        }

        if (page.value === total.value) {
            disabled.value = true;
        }

    }
};


const conditionFilter = computed(() =>
    recordData.value.filter(
        (data) =>
            (!search.value || data.record_id.toLowerCase().includes(search.value.toLowerCase())) &&
            (!filterState.value || data.state === filterState.value) &&
            (!router.currentRoute.value.query.project_name || data.project_name === router.currentRoute.value.query.project_name)
    )

)
const filter = computed(() =>
    conditionFilter.value.slice(0, page.value)

)

const formatUncertainty = (row, column, cellValue) => {
    if (typeof cellValue === 'number') {
        // 将浮点数转换为字符串，并截取前五位
        return cellValue.toFixed(5);
    }
    return cellValue;
};

class InfiniteColorDictionary {
    constructor() {
        this.colorDictionary = {};
    }

    // 获取键对应的颜色，如果不存在则创建新颜色
    getColorForKey(key) {
        if (this.colorDictionary.hasOwnProperty(key)) {
            // 如果键存在，则返回对应的颜色
            return this.colorDictionary[key];
        } else {
            // 如果键不存在，则创建新颜色并存储
            const newColor = this.generateRandomColor();
            this.colorDictionary[key] = newColor;
            return newColor;
        }
    }


    hexToRgb(hex) {
        // 去掉可能存在的 '#' 符号
        hex = hex.replace(/^#/, '');

        // 将十六进制分解为R、G、B值
        const bigint = parseInt(hex, 16);
        const r = (bigint >> 16) & 255;
        const g = (bigint >> 8) & 255;
        const b = bigint & 255;

        // 返回RGB格式的字符串
        return `rgb(${r}, ${g}, ${b}, 0.3)`;
    }

    // 生成一个随机颜色
    generateRandomColor() {
        const letters = '0123456789ABCDEF';
        let color = '#';
        for (let i = 0; i < 6; i++) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return this.hexToRgb(color);
    }
}

const colorDictionary = new InfiniteColorDictionary();

const onDialogOpened = () => {
    console.log(selectedRecord)
    const image = new Image();

    image.src = selectedRecord.value.image_shared_url

    const canvas = canvasRef.value;

    const ctx = canvas.getContext('2d');

    canvas.width = image.width;
    canvas.height = image.height;

    dialogWidth.value = canvas.width + 40

    ctx.drawImage(image, 0, 0, image.width, image.height) // 在画布上定位图像，并规定图像的宽度和高度

    for (const item of selectedRecord.value.bboxes) {
        const x1 = item.box.x1
        const x2 = item.box.x2
        const y1 = item.box.y1
        const y2 = item.box.y2
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1) // 矩形的位置（x1, y1）宽（x2-x1）高（y2-y1）

        ctx.fillStyle = colorDictionary.getColorForKey(item.name); // 红色半透明
        ctx.fillRect(x1, y1, x2 - x1, y2 - y1); // 从 (50, 50) 开始，绘制一个宽高为 100x100 的矩形
    }

    // ctx.fillStyle = 'rgba(255, 0, 0, 0.5)'; // 红色半透明
    // ctx.fillRect(50, 50, 100, 100); // 从 (50, 50) 开始，绘制一个宽高为 100x100 的矩形
}


const openImageDialog = (row, event, column) => {
    selectedRecord.value = recordData.value.find(record => record.record_id === row.record_id)
    dialogVisible.value = true

    console.log(selectedRecord.value)
};


const filterState = ref('')

const search = ref('');
const loading = ref(true)

const statusFilters = ref([{ label: 'INVALID', value: 'invalid' },
{ label: 'AUTO', value: 'auto_annotation_completed' },
{ label: 'ORA', value: 'pending_oracle_annotation' },
{ label: 'INIT', value: 'initialization' },
{ label: 'HUMAN', value: 'human_annotation_completed' }])


const stringify = (bboxes) => {
    return JSON.stringify(bboxes)
}


const reocordDelete = (row) => {
    request.delete(`/api/v1/de/records/${row.record_id}`).then((response) => {
        recordData.value = recordData.value.filter(recordData => recordData.record_id !== row.record_id)
    })
}

onMounted(
    () => {
        tableHeight.value = window.innerHeight * 0.75
    }
)

</script>
