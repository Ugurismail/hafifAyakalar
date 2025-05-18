// static/js/question_map.js

document.addEventListener('DOMContentLoaded', function () {
    // Global değişkenler
    var width = document.getElementById('chart').clientWidth;
    var height = 800; // İhtiyacınıza göre ayarlayın
    var svg, g, zoom;
    var link, node, label;
    var simulation;
    var questionData;
    var selectedUsers = [];
    var focusQuestionId = getParameterByName('question_id'); // URL'den question_id parametresini al

    // Başlatma fonksiyonu
    function init() {
        // SVG ve grup elemanlarını oluşturun
        svg = d3.select("#chart")
            .append("svg")
            .attr("width", width)
            .attr("height", height);

        g = svg.append("g");

        // Zoom davranışını tanımlayın
        zoom = d3.zoom()
            .scaleExtent([0.05, 5])
            .on("zoom", function (event) {
                g.attr("transform", event.transform);
                updateNodeVisibility(event.transform.k);
            });

        svg.call(zoom);

        // Ok işaretlerini tanımlayın
        var defs = svg.append("defs");
        defs.append("marker")
            .attr("id", "arrowhead")
            .attr("viewBox", "-0 -5 10 10")
            .attr("refX", 25)
            .attr("refY", 0)
            .attr("orient", "auto")
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", "#999");

        // İlk veri yüklemesi (tüm sorular)
        fetchData('/map-data/', function(data) {
            questionData = data;
            createGraph();
        });

        // Buton olaylarını tanımlayın
        setupButtons();

        // Kullanıcı arama işlevselliğini tanımlayın
        setupUserSearch();
    }

    // Veri çekme fonksiyonu
    function fetchData(url, callback) {
        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            callback(data);
        });
    }

    // Grafiği oluşturma fonksiyonu
    function createGraph() {
        // Simülasyonu başlatın
        simulation = d3.forceSimulation(questionData.nodes)
            .force("link", d3.forceLink(questionData.links)
                .id(function (d) { return d.id; })
                .distance(150)
            )
            .force("charge", d3.forceManyBody()
                .strength(-200)
            )
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collide", d3.forceCollide()
                .radius(function (d) { return d.size * 1.5; })
            )
            .on('end', function() {
                if (focusQuestionId) {
                    var targetNode = questionData.nodes.find(node => node.question_id.toString() === focusQuestionId);
                    if (targetNode) {
                        zoomToNode(targetNode);
                    }
                }
            });

        // Bağlantıları oluşturun
        link = g.append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(questionData.links)
            .enter().append("line")
            .attr("stroke-width", 2)
            .attr("stroke", "#999")
            .attr("marker-end", "url(#arrowhead)");

        // Düğümleri oluşturun
        node = g.append("g")
            .attr("class", "nodes")
            .selectAll("circle")
            .data(questionData.nodes)
            .enter().append("circle")
            .attr("r", function (d) { return d.size; })
            .attr("fill", function (d) {
                if (d.users.length > 1) {
                    return "#A9A9A9"; // Ortak sorular için gri renk
                } else {
                    return d.color; // Kullanıcıya özel renk
                }
            })
            .on("click", function (event, d) {
                window.location.href = "/question/" + d.question_id + "/";
            })
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended)
            );

        // Etiketleri oluşturun
        var TBAS_COLOR = getComputedStyle(document.documentElement).getPropertyValue('--tbas-color') || "#000000";
        TBAS_COLOR = TBAS_COLOR.trim();
        console.log("Aktif TBAS_COLOR", TBAS_COLOR);
        
        label = g.append("g")
            .attr("class", "labels")
            .selectAll("text")
            .data(questionData.nodes)
            .enter().append("text")
            .attr("dy", -10)
            .attr("text-anchor", "middle")
            .text(function (d) { return d.label; })
            .style("font-size", function (d) {
                return (12 + (d.users.length * 2)) + "px";
            })
            .style("fill", TBAS_COLOR);
        

        // Simülasyonu başlatın
        simulation.on("tick", ticked);

        // Maksimum kullanıcı sayısını hesaplayın
        questionData.maxUserCount = d3.max(questionData.nodes, function(d) { return d.users.length; }) || 1;

        // Düğüm görünürlüğünü başlatın
        updateNodeVisibility(1);
    }

    // Simülasyon "tick" fonksiyonu
    function ticked() {
        link
            .attr("x1", function (d) { return d.source.x; })
            .attr("y1", function (d) { return d.source.y; })
            .attr("x2", function (d) { return d.target.x; })
            .attr("y2", function (d) { return d.target.y; });

        node
            .attr("cx", function (d) { return d.x; })
            .attr("cy", function (d) { return d.y; });

        label
            .attr("x", function (d) { return d.x; })
            .attr("y", function (d) { return d.y - d.size - 5; });
    }

    // Düğüm görünürlüğünü güncelleme fonksiyonu
    function updateNodeVisibility(zoomLevel) {
        node.each(function(d) {
            var minOpacity = 0.8;
            var maxOpacity = 0.9;
            var userCountFactor = (d.users.length - 1) / (questionData.maxUserCount - 1) || 0;
            var opacity = minOpacity + (maxOpacity - minOpacity) * userCountFactor;

            if (zoomLevel < 0.5) {
                opacity = opacity * zoomLevel * 2;
            }
            d.opacity = opacity;

            d3.select(this).style("opacity", d.opacity);
        });

        label.each(function(d) {
            d3.select(this).style("opacity", d.opacity);
        });

        label.style("font-size", function(d) {
            var baseSize = 12 + (d.users.length * 2);
            return baseSize * zoomLevel + "px";
        });
    }

    // Sürükleme fonksiyonları
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
    }

    // Haritayı belirli bir düğüme yakınlaştırma fonksiyonu
    function zoomToNode(node) {
        var scale = 1.5;
        var x = -node.x * scale + width / 2;
        var y = -node.y * scale + height / 2;
        svg.transition()
            .duration(750)
            .call(zoom.transform, d3.zoomIdentity.translate(x, y).scale(scale));
    }

    // Buton olaylarını tanımlama fonksiyonu
    function setupButtons() {
        // "Ben" butonu
        document.getElementById('btn-me').addEventListener('click', function () {
            // Clear selected users
            selectedUsers = [];
            document.getElementById('selected-users-list').innerHTML = '';
        
            fetchData('/map-data/?filter=me', function(data) {
                questionData = data;
                updateGraph();
            });
        });

        // "Tümü" butonu
        document.getElementById('btn-all').addEventListener('click', function () {
            // Clear selected users
            selectedUsers = [];
            document.getElementById('selected-users-list').innerHTML = '';
        
            fetchData('/map-data/', function(data) {
                questionData = data;
                updateGraph();
            });
        });

        // "Filtrele" butonu
        document.getElementById('btn-filter-users').addEventListener('click', function () {
            if (selectedUsers.length > 0) {
                var params = selectedUsers.map(function(id) {
                    return 'user_id=' + id;
                }).join('&');
                fetchData('/map-data/?' + params, function(data) {
                    questionData = data;
                    updateGraph();
                });
            }
        });

    }

    function setupUserSearch() {
        var userSearchInput = document.getElementById('user-search-input');
        var userSearchResults = document.getElementById('user-search-results');
        var selectedUsersList = document.getElementById('selected-users-list');
    
        userSearchInput.addEventListener('input', function () {
            var query = this.value;
            if (query.length > 0) {
                fetch('/user-search/?q=' + encodeURIComponent(query), {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    userSearchResults.innerHTML = '';
                    if (data.results.length > 0) {
                        data.results.forEach(function (user) {
                            var div = document.createElement('div');
                            div.classList.add('list-group-item');
                            div.textContent = user.username;
                            div.dataset.userId = user.id;
                            userSearchResults.appendChild(div);
                        });
                        userSearchResults.style.display = 'block';
                    } else {
                        userSearchResults.style.display = 'none';
                    }
                });
            } else {
                userSearchResults.style.display = 'none';
            }
        });
    
        // Handle clicks on search results
        userSearchResults.addEventListener('click', function(event) {
            var target = event.target;
            if (target && target.matches('.list-group-item')) {
                var userId = target.dataset.userId;
                var username = target.textContent;
    
                // Add user to selected list
                if (!selectedUsers.includes(userId)) {
                    selectedUsers.push(userId);
                    addUserToSelectedList(userId, username);
                }
    
                userSearchInput.value = '';
                userSearchResults.style.display = 'none';
            }
        });
    
        // Hide search results when clicking outside
        document.addEventListener('click', function(event) {
            if (!event.target.closest('#user-search-input') && !event.target.closest('#user-search-results')) {
                userSearchResults.style.display = 'none';
            }
        });
    }

    // Seçili kullanıcılar listesine ekleme fonksiyonu
    function addUserToSelectedList(userId, username) {
        var userList = document.getElementById('selected-users-list');
        var li = document.createElement('li');
        li.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center');
        li.textContent = username;
        li.dataset.userId = userId;

        var removeBtn = document.createElement('button');
        removeBtn.classList.add('btn', 'btn-sm', 'btn-danger');
        removeBtn.textContent = 'Kaldır';
        removeBtn.addEventListener('click', function () {
            selectedUsers = selectedUsers.filter(function (id) {
                return id !== userId;
            });
            userList.removeChild(li);
        });

        li.appendChild(removeBtn);
        userList.appendChild(li);
    }

    // Grafiği güncelleme fonksiyonu
    function updateGraph() {
        // Simülasyonu durdurun
        simulation.stop();

        // Mevcut elemanları kaldırın
        g.selectAll("*").remove();

        // Grafiği yeniden oluşturun
        createGraph();
    }

    // URL parametresini alma fonksiyonu
    function getParameterByName(name) {
        var url = window.location.href;
        name = name.replace(/[\\[\\]]/g, "\\$&");
        var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)");
        var results = regex.exec(url);
        if (!results) return null;
        if (!results[2]) return '';
        return decodeURIComponent(results[2].replace(/\\+/g, " "));
    }

    // Başlatma fonksiyonunu çağırın
    init();
});
