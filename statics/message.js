export default {
    props: {
        messages: Array,
    },
    emits: ['clicked'],
    methods: {
        sendHistory(slug) {
            this.$emit('clicked', slug);
        }
    },
    updated() {
        const messageArea = document.querySelector('#messageArea');
        messageArea.scrollTop = messageArea.scrollHeight;
    },
    template: `
    <template v-for="msg in messages">
        <div class="textMsg output" v-if="msg.from === 'init' && msg.type === 1">
            <div class="card">
                <div class="card-body">
                    您好，歡迎來到 SeaBelt 推薦平台！
                </div>
            </div>
        </div>

        <div class="textMsg output" v-else-if="msg.from === 'init' && msg.type === 2">
            <div class="card">
                <div class="card-body">
                    SeaBelt 蒐集了知名 NFT 商品公開交易平台 - OpenSea 網站的商品資料，並整理成以下6項類別：
                    <ul>
                        <li>art (藝術)</li>
                        <li>avatar (角色)</li>
                        <li>discount (折扣)</li>
                        <li>experience (特殊體驗)</li>
                        <li>limited items (限量商品)</li>
                        <li>virtual world (虛擬世界)</li>
                    </ul>
                    只要輸入你想要尋找的商品類別，SeaBelt 就會為您推薦符合的NFT商品。
                </div>
            </div>
        </div>

        <div :class="msg.from === 'input' ? 'textMsg input' : 'textMsg output'" v-else-if="msg.type === 'text'">
            <div class="card">
                <div class="card-body">
                    {[ msg.content ]}
                </div>
            </div>
        </div>

        <div :id="'productCarousel-' + msg.id" class="carousel slide productMsg output" data-bs-ride="carousel"
        data-bs-wrap="false" v-else-if="msg.type === 'product'">
            <div class="carousel-inner">
                <template v-for="(four_items, index) in msg.content">
                    <div :class="index === 0 ? 'carousel-item active' : 'carousel-item'">
                        <div class="card-group">
                            <template v-for="item in four_items">
                                <a :href="'https://opensea.io/collection/' + item['collection-slug']"
                                    :title="item['collection-slug']" target="_blank" @click="sendHistory(item['collection-slug'])">
                                    <div class="card">
                                        <img :src="item['collection-image']" class="card-img-top"
                                            :alt="item['collection-slug']">
                                        <div class="card-body">
                                            <h5 class="card-title">{[ item['collection-name'] ]}</h5>
                                            <p class="card-text">{[ item['collection-description'] ]}</p>
                                        </div>
                                        <div class="card-footer">
                                            <span class="badge bg-warning text-dark" v-for="label in item['labels']">
                                                {[ label ]}
                                            </span>
                                        </div>
                                    </div>
                                </a>
                            </template>
                        </div>
                    </div>
                </template>
            </div>
            <button class="carousel-control-prev" type="button" :data-bs-target="'#productCarousel-' + msg.id"
                data-bs-slide="prev">
                <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                <span class="visually-hidden">Previous</span>
            </button>
            <button class="carousel-control-next" type="button" :data-bs-target="'#productCarousel-' + msg.id"
                data-bs-slide="next">
                <span class="carousel-control-next-icon" aria-hidden="true"></span>
                <span class="visually-hidden">Next</span>
            </button>
        </div>
    </template>
    `,
    delimiters: ['{[', ']}'],
}