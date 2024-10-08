//VARIÁVEL GLOBAL
var url_atual = window.location.pathname; //Full Path
var url_sem_slug = url_atual.split('/');
var url_sem_slug = url_sem_slug[1];

//Sidebar
$(document).ready(function() {
    const sidebar = document.querySelector('.sidebar');
    const dropdownButtons = document.querySelectorAll('.dropdown-toggle');
    
    // Função para ocultar/mostrar os dropdowns com base no estado da sidebar
    function toggleDropdowns() {
        const dropdowns = document.querySelectorAll('.dropdown-menu');
        if (sidebar.classList.contains('collapsed')) {
            dropdowns.forEach(dropdown => {
                dropdown.style.display = 'none'; // Oculta o dropdown quando a sidebar está colapsada
            });
        }
    }
    
    // Inicializa o estado da sidebar e dos dropdowns ao carregar a página
    toggleDropdowns();

    // Detecta quando o mouse entra na sidebar
    sidebar.addEventListener('mouseenter', function() {
        sidebar.classList.remove('collapsed'); // Expande a sidebar
        toggleDropdowns(); // Atualiza o estado dos dropdowns
    });

    // Detecta quando o mouse sai da sidebar
    sidebar.addEventListener('mouseleave', function() {
        sidebar.classList.add('collapsed'); // Colapsa a sidebar
        toggleDropdowns(); // Atualiza o estado dos dropdowns
    });

    // Adiciona evento de clique para os botões de dropdown
    dropdownButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            const dropdownMenu = button.nextElementSibling; // Pega o próximo elemento (dropdown-menu)

            // Fecha todos os outros dropdowns antes de abrir o novo
            const allDropdowns = document.querySelectorAll('.dropdown-menu');
            allDropdowns.forEach(dropdown => {
                if (dropdown !== dropdownMenu) {
                    dropdown.style.display = 'none'; // Fecha outros dropdowns
                }
            });
            
            // Verifica se a sidebar está expandida
            if (!sidebar.classList.contains('collapsed')) {
                // Alterna a visibilidade do dropdown correspondente
                const isVisible = dropdownMenu.style.display === 'block';
                dropdownMenu.style.display = isVisible ? 'none' : 'block';
            }
            event.stopPropagation(); // Impede que o clique se propague
        });
    });

    // Fecha todos os dropdowns quando clicar fora
    document.addEventListener('click', function() {
        const dropdowns = document.querySelectorAll('.dropdown-menu');
        dropdowns.forEach(dropdown => {
            dropdown.style.display = 'none'; // Oculta todos os dropdowns
        });
    });
});

//FimSidebar

//Funções tela de vendas
if (url_sem_slug == "/vendas/"){
    //////////////////////////////////////////////////////   
}

//Funções tela de conferir_vendas_geral
if (url_sem_slug == "/conferir_vendas_geral/"){
    //////////////////////////////////////////////////////
    //Modal Excluir Venda tela de Conferir Vendas Geral
    function excluirVenda(slugvenda){
        Swal.fire({
            "title": "Tem certeza ?",
            "text": "Essa ação não pode ser desfeita",
            "icon": "question",
            "showCancelButton": true,
            "showCloseButton": true,
            "cancelButtonText": "Não, Cancelar",
            "confirmButtonText": "Sim, Excluir",
            "reverseButtons": true,
            "confirmButtonColor": "#dc3545",
            "focusConfirm": true,
            "allowEscapeKey": false,
            "allowEnterKey": false,
            "allowOutsideClick": false
        })
        .then(function(result){
            if(result.isConfirmed) {
                window.location.pathname = "excluir_venda/" + slugvenda + "/"
            }
        })
    }

    //Modal Confirmar Venda tela de Vendas finalizadas
    function confirmarVenda(element){
        var slugvenda = element.getAttribute('data-slug');
        var forloopCounter = element.getAttribute('data-counter');
        Swal.fire({
            "title": "Tem certeza ?",
            "text": "Essa ação não pode ser desfeita",
            "icon": "question",
            "showCancelButton": true,
            "showCloseButton": true,
            "cancelButtonText": "Não, Cancelar",
            "confirmButtonText": "Sim, Confirmar",
            "reverseButtons": true,
            "confirmButtonColor": "#28a745",
            "focusConfirm": true,
            "allowEscapeKey": false,
            "allowEnterKey": false,
            "allowOutsideClick": false
        })
        .then(function(result){ // Aqui abaixo estou pegando os valores de valor_pago e troco pra enviar pro backend na URL
            if (result.isConfirmed) {
                var valorPago = document.getElementById("valor_pago_" + forloopCounter).value;
                var troco = document.getElementById("troco" + forloopCounter).value;
                
                // Construa a URL com os parâmetros de consulta (query parameters)
                var url = "/confirmar_venda/" + slugvenda + "/?valor_pago=" + valorPago + "&troco=" + troco;

                // Redirecione para a URL construída
                window.location.href = url;
            }
        })
    }
}

//Funções tela de vendas_finalizadas
if (url_sem_slug == "vendas_finalizadas"){
    //////////////////////////////////////////////////////
    //Modal Excluir Venda tela de Vendas finalizadas
    function excluirVenda(element){
        var slugvenda = element.getAttribute('data-slug');
        Swal.fire({
            "title": "Tem certeza ?",
            "text": "Essa ação não pode ser desfeita",
            "icon": "question",
            "showCancelButton": true,
            "showCloseButton": true,
            "cancelButtonText": "Não, Cancelar",
            "confirmButtonText": "Sim, Excluir",
            "reverseButtons": true,
            "confirmButtonColor": "#dc3545",
            "focusConfirm": true,
            "allowEscapeKey": false,
            "allowEnterKey": false,
            "allowOutsideClick": false
        })
        .then(function(result){
            if(result.isConfirmed) {
                window.location.pathname = "excluir_venda_geral/" + slugvenda + "/"
            }
        })
    }

    //Modal Confirmar Venda tela de Vendas finalizadas
    function confirmarVenda(element){
        var slugvenda = element.getAttribute('data-slug');
        var forloopCounter = element.getAttribute('data-counter');
        Swal.fire({
            "title": "Tem certeza ?",
            "text": "Essa ação não pode ser desfeita",
            "icon": "question",
            "showCancelButton": true,
            "showCloseButton": true,
            "cancelButtonText": "Não, Cancelar",
            "confirmButtonText": "Sim, Confirmar",
            "reverseButtons": true,
            "confirmButtonColor": "#28a745",
            "focusConfirm": true,
            "allowEscapeKey": false,
            "allowEnterKey": false,
            "allowOutsideClick": false
        })
        .then(function(result){ // Aqui abaixo estou pegando os valores de valor_pago, troco e quantidade_parcelas pra enviar pro backend na URL
            if (result.isConfirmed) {
                var valorPago = document.getElementById("valor_pago_" + forloopCounter).value;
                var troco = document.getElementById("troco" + forloopCounter).value;
                var QuantidadeParcelas = document.getElementById("quantidade_parcelas" + forloopCounter).value;

                // Construa a URL com os parâmetros de consulta (query parameters)
                var url = "/confirmar_venda_geral/" + slugvenda + "/?valor_pago=" + valorPago + "&troco=" + troco + "&quantidade_parcelas=" + QuantidadeParcelas;

                // Redirecione para a URL construída
                window.location.href = url;
            }
        })
    }
}

//Funções tela de editar_vendas
if (url_sem_slug == "/editar_vendas/"){
    //////////////////////////////////////////////////////
    //Modal Cancelar Venda tela editar_vendas
    function ExcluirVenda(slugvenda){
        Swal.fire({
            "title": "Tem certeza ?",
            "text": "Essa ação não pode ser desfeita",
            "icon": "question",
            "showCancelButton": true,
            "showCloseButton": true,
            "cancelButtonText": "Não, Cancelar",
            "confirmButtonText": "Sim, Excluir",
            "reverseButtons": true,
            "confirmButtonColor": "#dc3545",
            "focusConfirm": true,
            "allowEscapeKey": false,
            "allowEnterKey": false,
            "allowOutsideClick": false
        })
        .then(function(result){
            if(result.isConfirmed) {
                window.location.pathname = "excluir_venda_geral_pos/" + slugvenda + "/"
            }
        })
    }

    //Modal Estornar Venda tela editar_vendas
    function EstornarVenda(slugvenda){
        Swal.fire({
            "title": "Tem certeza ?",
            "text": "Essa ação não pode ser desfeita",
            "icon": "question",
            "showCancelButton": true,
            "showCloseButton": true,
            "cancelButtonText": "Não, Cancelar",
            "confirmButtonText": "Sim, Estornar",
            "reverseButtons": true,
            "confirmButtonColor": "#28a745",
            "focusConfirm": true,
            "allowEscapeKey": false,
            "allowEnterKey": false,
            "allowOutsideClick": false
        })
        .then(function(result){
            if(result.isConfirmed) {
                window.location.pathname = "estornar_venda_geral_pos/" + slugvenda + "/"
            }
        })
    }

    //Modal Excluir Venda tela editar_vendas
    function TrocarVenda(slugvenda){
        Swal.fire({
            "title": "Tem certeza ?",
            "text": "Essa ação não pode ser desfeita",
            "icon": "question",
            "showCancelButton": true,
            "showCloseButton": true,
            "cancelButtonText": "Não, Cancelar",
            "confirmButtonText": "Sim, Trocar",
            "reverseButtons": true,
            "confirmButtonColor": "#28a745",
            "focusConfirm": true,
            "allowEscapeKey": false,
            "allowEnterKey": false,
            "allowOutsideClick": false
        })
        .then(function(result){
            if(result.isConfirmed) {
                window.location.pathname = "/" + slugvenda + "/"
            }
        })
    }
}

//Funções tela de Ações individuais das vendas pós finalização
if (url_atual.substring(0, url_sem_slug.length - 9) == "/acoes_vendas/"){
    //////////////////////////////////////////////////////
    //Modal Cancelamento individual de venda - tela ações vendas
    function ExcluirVenda(slugvenda){
        Swal.fire({
            "title": "Tem certeza ?",
            "text": "Essa ação não pode ser desfeita",
            "icon": "question",
            "showCancelButton": true,
            "showCloseButton": true,
            "cancelButtonText": "Não, Cancelar",
            "confirmButtonText": "Sim, Excluir",
            "reverseButtons": true,
            "confirmButtonColor": "#dc3545",
            "focusConfirm": true,
            "allowEscapeKey": false,
            "allowEnterKey": false,
            "allowOutsideClick": false
        })
        .then(function(result){
            if(result.isConfirmed) {
                window.location.pathname = "excluir_venda_pos/" + slugvenda + "/"
            }
        })
    }

    //Modal Estorno individual de venda - tela ações vendas
    function EstornarVenda(slugvenda){
        Swal.fire({
            "title": "Tem certeza ?",
            "text": "Essa ação não pode ser desfeita",
            "icon": "question",
            "showCancelButton": true,
            "showCloseButton": true,
            "cancelButtonText": "Não, Cancelar",
            "confirmButtonText": "Sim, Estornar",
            "reverseButtons": true,
            "confirmButtonColor": "#28a745",
            "focusConfirm": true,
            "allowEscapeKey": false,
            "allowEnterKey": false,
            "allowOutsideClick": false
        })
        .then(function(result){
            if(result.isConfirmed) {
                window.location.pathname = "estornar_venda_pos/" + slugvenda + "/"
            }
        })
    }

    //Modal Troca individual de venda - tela ações vendas
    function TrocarVenda(slugvenda){
        Swal.fire({
            "title": "Tem certeza ?",
            "text": "Essa ação não pode ser desfeita",
            "icon": "question",
            "showCancelButton": true,
            "showCloseButton": true,
            "cancelButtonText": "Não, Cancelar",
            "confirmButtonText": "Sim, Trocar",
            "reverseButtons": true,
            "confirmButtonColor": "#28a745",
            "focusConfirm": true,
            "allowEscapeKey": false,
            "allowEnterKey": false,
            "allowOutsideClick": false
        })
        .then(function(result){
            if(result.isConfirmed) {
                window.location.pathname = "/" + slugvenda + "/"
            }
        })
    }
}

//Funções tela dos produtos
if (url_sem_slug == "add_produto"){
//////////////////////////////////////////////////////
  // Extrai os valores da query string e preenche os campos #Teste pra preencher os campos após POST
  //Adicionar value="{{quantidade}}" por exemplo no campo.
    var params = new URLSearchParams(window.location.search);
    document.getElementsByName('quantidade')[0].value = params.get('quantidade') || '';
    document.getElementsByName('preco_compra')[0].value = params.get('preco_compra') || '';
    document.getElementsByName('peso')[0].value = params.get('peso') || '';
//////////////////////////////////////////////////////
//Modal Excluir Produto tela de Cadastro de Produtos
function excluirProduto(slugproduto){
    Swal.fire({
        "title": "Tem certeza ?",
        "text": "Essa ação não pode ser desfeita",
        "icon": "question",
        "showCancelButton": true,
        "showCloseButton": true,
        "cancelButtonText": "Não, Cancelar",
        "confirmButtonText": "Sim, Excluir",
        "reverseButtons": true,
        "confirmButtonColor": "#dc3545",
        "focusConfirm": true,
        "allowEscapeKey": false,
        "allowEnterKey": false,
        "allowOutsideClick": false
    })
    .then(function(result){
        if(result.isConfirmed) {
            window.location.pathname = "excluir_produto/" + slugproduto + "/"
        }
    })
}
}

//Funções tela das categorias
if (url_sem_slug == "/add_categoria/"){
    //////////////////////////////////////////////////////
    //Modal Excluir Categoria tela de Cadastro de Categorias
    function excluirCategoria(slugcategoria){
        Swal.fire({
            "title": "Tem certeza ?",
            "text": "Essa ação não pode ser desfeita",
            "icon": "question",
            "showCancelButton": true,
            "showCloseButton": true,
            "cancelButtonText": "Não, Cancelar",
            "confirmButtonText": "Sim, Excluir",
            "reverseButtons": true,
            "confirmButtonColor": "#dc3545",
            "focusConfirm": true,
            "allowEscapeKey": false,
            "allowEnterKey": false,
            "allowOutsideClick": false
        })
        .then(function(result){
            if(result.isConfirmed) {
                window.location.pathname = "excluir_categoria/" + slugcategoria + "/"
            }
        })
    }
}

//Funções tela das cores
if (url_sem_slug == "/add_cor/"){
    //////////////////////////////////////////////////////
    //Modal Excluir Cor tela de Cadastro de cores
    function excluirCor(slugcor){
        Swal.fire({
            "title": "Tem certeza ?",
            "text": "Essa ação não pode ser desfeita",
            "icon": "question",
            "showCancelButton": true,
            "showCloseButton": true,
            "cancelButtonText": "Não, Cancelar",
            "confirmButtonText": "Sim, Excluir",
            "reverseButtons": true,
            "confirmButtonColor": "#dc3545",
            "focusConfirm": true,
            "allowEscapeKey": false,
            "allowEnterKey": false,
            "allowOutsideClick": false
        })
        .then(function(result){
            if(result.isConfirmed) {
                window.location.pathname = "excluir_cor/" + slugcor + "/"
            }
        })
    }
}

//Funções tela dos tamanhos
if (url_sem_slug == "/add_tamanho/"){
    //////////////////////////////////////////////////////
    //Modal Excluir Tamanho tela de Cadastro de Tamanhos
    function excluirTamanho(slugtamanho){
        Swal.fire({
            "title": "Tem certeza ?",
            "text": "Essa ação não pode ser desfeita",
            "icon": "question",
            "showCancelButton": true,
            "showCloseButton": true,
            "cancelButtonText": "Não, Cancelar",
            "confirmButtonText": "Sim, Excluir",
            "reverseButtons": true,
            "confirmButtonColor": "#dc3545",
            "focusConfirm": true,
            "allowEscapeKey": false,
            "allowEnterKey": false,
            "allowOutsideClick": false
        })
        .then(function(result){
            if(result.isConfirmed) {
                window.location.pathname = "excluir_tamanho/" + slugtamanho + "/"
            }
        })
    }
}

//Funções tela dos Nome dos Produtos
if (url_sem_slug == "add_novonome_produto"){
    //////////////////////////////////////////////////////
    //Modal Excluir Nome dos Produtos tela de Cadastro de Nome dos Produtos
    function excluirNomeProduto(slugnomeproduto){
        Swal.fire({
            "title": "Tem certeza ?",
            "text": "Essa ação não pode ser desfeita",
            "icon": "question",
            "showCancelButton": true,
            "showCloseButton": true,
            "cancelButtonText": "Não, Cancelar",
            "confirmButtonText": "Sim, Excluir",
            "reverseButtons": true,
            "confirmButtonColor": "#dc3545",
            "focusConfirm": true,
            "allowEscapeKey": false,
            "allowEnterKey": false,
            "allowOutsideClick": false
        })
        .then(function(result){
            if(result.isConfirmed) {
                window.location.pathname = "excluir_novonome_produto/" + slugnomeproduto + "/"
            }
        })
    }
}


//Funções tela de Cadastro de Familias
if (url_sem_slug == "cadastrar_familia"){
    //////////////////////////////////////////////////////
    //Modal Excluir Familia tela de Cadastro de Familias
    function excluirfamilia(idfamilia){
        Swal.fire({
            "title": "Tem certeza ?",
            "text": "Essa ação não pode ser desfeita",
            "icon": "question",
            "showCancelButton": true,
            "showCloseButton": true,
            "cancelButtonText": "Não, Cancelar",
            "confirmButtonText": "Sim, Excluir",
            "reverseButtons": true,
            "confirmButtonColor": "#dc3545",
            "focusConfirm": true,
            "allowEscapeKey": false,
            "allowEnterKey": false,
            "allowOutsideClick": false
        })
        .then(function(result){
            if(result.isConfirmed) {
                window.location.pathname = "excluir_familia/" + idfamilia + "/"
            }
        })
    }


    function inativarfamilia(idfamilia){
        Swal.fire({
            "title": "Tem certeza ?",
            "icon": "question",
            "showCancelButton": true,
            "showCloseButton": true,
            "cancelButtonText": "Não, Cancelar",
            "confirmButtonText": "Sim, Inativar",
            "reverseButtons": true,
            "confirmButtonColor": "#dc3545",
            "focusConfirm": true,
            "allowEscapeKey": false,
            "allowEnterKey": false,
            "allowOutsideClick": false
        })
        .then(function(result){
            if(result.isConfirmed) {
                window.location.pathname = "inativar_familia/" + idfamilia + "/"
            }
        })
    }

    function ativarfamilia(idfamilia){
        Swal.fire({
            "title": "Tem certeza ?",
            "icon": "question",
            "showCancelButton": true,
            "showCloseButton": true,
            "cancelButtonText": "Não, Cancelar",
            "confirmButtonText": "Sim, ativar",
            "reverseButtons": true,
            "confirmButtonColor": "#dc3545",
            "focusConfirm": true,
            "allowEscapeKey": false,
            "allowEnterKey": false,
            "allowOutsideClick": false
        })
        .then(function(result){
            if(result.isConfirmed) {
                window.location.pathname = "ativar_familia/" + idfamilia + "/"
            }
        })
    }
}


//Funções tela de Cadastro de Vendedores
if (url_sem_slug == "cadastrar_vendedor"){
    //////////////////////////////////////////////////////
    //Modal Excluir Vendedor tela de Cadastro de Vendedores
    function excluirVendedor(idvendedor){
        Swal.fire({
            "title": "Tem certeza ?",
            "text": "Essa ação não pode ser desfeita",
            "icon": "question",
            "showCancelButton": true,
            "showCloseButton": true,
            "cancelButtonText": "Não, Cancelar",
            "confirmButtonText": "Sim, Excluir",
            "reverseButtons": true,
            "confirmButtonColor": "#dc3545",
            "focusConfirm": true,
            "allowEscapeKey": false,
            "allowEnterKey": false,
            "allowOutsideClick": false
        })
        .then(function(result){
            if(result.isConfirmed) {
                window.location.pathname = "excluir_vendedor/" + idvendedor + "/"
            }
        })
    }
}


//Funções tela de Cadastro do Responsável Geral
if (url_sem_slug == "cadastrar_responsavel"){
    //////////////////////////////////////////////////////
    //Modal Excluir Responsável tela de Cadastro do Responsável Geral
    function excluirResponsavelGeral(idresponsavel){
        Swal.fire({
            "title": "Tem certeza ?",
            "text": "Essa ação não pode ser desfeita",
            "icon": "question",
            "showCancelButton": true,
            "showCloseButton": true,
            "cancelButtonText": "Não, Cancelar",
            "confirmButtonText": "Sim, Excluir",
            "reverseButtons": true,
            "confirmButtonColor": "#dc3545",
            "focusConfirm": true,
            "allowEscapeKey": false,
            "allowEnterKey": false,
            "allowOutsideClick": false
        })
        .then(function(result){
            if(result.isConfirmed) {
                window.location.pathname = "excluir_responsavel/geral/" + idresponsavel + "/"
            }
        })
    }
}

if (url_sem_slug == "/add_festa/"){
    // Extrai os valores da query string e preenche os campos
    //Adicionar value="{{quantidade}}" por exemplo no campo.
    var params = new URLSearchParams(window.location.search);
    document.getElementsByName('ano_festa')[0].value = params.get('ano_festa') || '';
    document.getElementsByName('edicao_festa')[0].value = params.get('edicao_festa') || '';
    document.getElementsByName('casal_festa')[0].value = params.get('casal_festa') || '';
    document.getElementsByName('casal_lojinha')[0].value = params.get('casal_lojinha') || '';
    document.getElementsByName('fornecedor_camisas')[0].value = params.get('fornecedor_camisas') || '';
    document.getElementsByName('fornecedor_produtos')[0].value = params.get('fornecedor_produtos') || '';
}