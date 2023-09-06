import { createApp } from 'vue';
import Message from './message.js';

// get cookie
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}
const lineId = getCookie('lineID');
const userName = getCookie('Name');
const userPicture = getCookie('icon');
let msgId = 0;


// main vue app
createApp({
    components: {
        Message
    },
    data() {
        return {
            lineId,
            userHistory: null,
            clickedHistory: '',
            messages: [
                {
                    id: msgId++,
                    from: 'init',
                    type: 1,
                    content: '歡迎來到SeaBelt推薦平台！'
                },
                {
                    id: msgId++,
                    from: 'init',
                    type: 2,
                    content: '只要輸入你想要尋找的商品類別，SeaBelt就會為您推薦符合的NFT商品。'
                },
            ],
            newInput: '',
        }
    },
    methods: {
        async loadHistory() {
            this.userHistory = await syncHistory('');
        },
        logout() {
            console.log('logout');
            document.cookie = 'Name=; expires=Thu, 01 Jan 1970 00:00:00 UTC;';
            document.cookie = 'lineID=; expires=Thu, 01 Jan 1970 00:00:00 UTC;';
            document.cookie = 'icon=; expires=Thu, 01 Jan 1970 00:00:00 UTC;';
            window.location.href = '/';
        },
        clearMessage() {
            this.messages = [];
        },
        async sendInput() {
            this.messages.push(
                {
                    id: msgId++,
                    from: 'input',
                    type: 'text',
                    content: this.newInput
                }
            );
            let result = await getReply(this.newInput, this.userHistory);
            this.newInput = '';
            console.log(`receive reply: ${Object.keys(result)}`)
            if (Object.keys(result).length === 0) {
                this.messages.push(
                    {
                        id: msgId++,
                        from: 'output',
                        type: 'text',
                        content: 'Oops！找不到符合的商品'
                    },
                );
            } else {
                for (let label in result) {
                    this.messages.push(
                        {
                            id: msgId++,
                            from: 'output',
                            type: 'text',
                            content: label === 'related' ? 'Oops！找不到符合的商品，或者您對以下商品會有興趣：'
                                : `為您找到 ${label} 類別的商品如下：`
                        },
                        {
                            id: msgId++,
                            from: 'output',
                            type: 'product',
                            content: result[label]
                        }
                    );
                }
            }
        },
    },
    watch: {
        async clickedHistory() {
            this.userHistory = await syncHistory(this.clickedHistory);
        }
    },
    created() {
        this.loadHistory();
    },
    delimiters: ['{[', ']}'],
}).mount('#app');


// fetch functions
async function syncHistory(inputText) {
    let data;
    try {
        data = await fetch(`/api/nft?slug=${inputText}&n=${userName}&i=${lineId}`)
    } catch (error) {
        console.error(error);
        showError();
    }
    return data.json();
}
async function getReply(inputText, userHistory) {
    let data;
    let lastHistory = userHistory.length > 0 ? userHistory[userHistory.length - 1]['collection-slug'] : '';

    disableInput(true);
    setTimeout(() => {
        toggleLoadingMessage(true);
    }, 500);

    try {
        data = await fetch(`/api/message?id=${lineId}&input=${inputText}&slug=${lastHistory}`)
    } catch (error) {
        console.error(error);
        showError();
    }

    disableInput(false);
    toggleLoadingMessage(false);

    return data.json();
}


// control elements display
function showError() {
    let myToast = document.querySelector('.toast');
    let toast = new bootstrap.Toast(myToast);
    toast.show();
}
function disableInput(bool) {
    let element = document.querySelector('#inputText');
    element.disabled ? element.removeAttribute('disabled') : element.setAttribute('disabled', 'disabled');
}
function toggleLoadingMessage(bool) {
    let element = document.querySelector('#loadingMessage');
    element.style.display = bool ? 'inline-block' : 'none';
}