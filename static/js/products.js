// Variables globales para paginación y búsqueda
let currentPage = 1;
let currentSearch = '';
let itemsPerPage = 10;

$(document).ready(function () {
  
  // Load products on page load
  loadProducts(currentPage, itemsPerPage, currentSearch);
  
  // Manejar búsqueda
  $("#search-btn").on("click", function() {
    currentSearch = $("#product-search").val().trim();
    currentPage = 1; // Resetear a la primera página al buscar
    loadProducts(currentPage, itemsPerPage, currentSearch);
  });
  
  // También permitir búsqueda al presionar Enter
  $("#product-search").on("keypress", function(e) {
    if (e.which === 13) {
      currentSearch = $(this).val().trim();
      currentPage = 1; // Resetear a la primera página al buscar
      loadProducts(currentPage, itemsPerPage, currentSearch);
    }
  });

  // Add product
  $("#save-product-btn").on("click", function () {
    const sku = $("#add-sku").val().trim();
    const name = $("#add-name").val().trim();
    const displayCase = $("#add-display-case").val().trim();
    const column = $("#add-column").val();
    const row = $("#add-row").val();

    if (!sku || !name || !displayCase || !column || !row) {
      alert("Por favor, complete todos los campos.");
      return;
    }

    // Check if SKU already exists before submitting
    checkSkuExists(sku.toUpperCase(), function (exists) {
      if (exists) {
        alert("El SKU ya existe. Por favor, utilice un SKU único.");
        return;
      }

      // If SKU is unique, proceed with adding the product
      $.ajax({
        url: "/api/products",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({
          sku: sku,
          name: name,
          display_case: displayCase,
          column: column,
          row: row,
        }),
        success: function (response) {
          if (response.success) {
            // Close modal and reset form
            $("#addProductModal").modal("hide");
            $("#add-product-form")[0].reset();

            // Reload products
            loadProducts(currentPage, itemsPerPage, currentSearch);
          }
        },
        error: function (xhr) {
          const response = xhr.responseJSON;
          alert(response.message || "Error al agregar el producto.");
        },
      });
    });
  });

  // Function to check if SKU exists
  function checkSkuExists(sku, callback) {
    $.ajax({
      url: "/api/products",
      type: "GET",
      success: function (products) {
        const exists = products.some((product) => product.sku === sku);
        callback(exists);
      },
      error: function () {
        // If there's an error, assume SKU doesn't exist to allow submission
        callback(false);
      },
    });
  }

  // Edit product - populate form
  $(document).on("click", ".edit-product", function () {
    const id = $(this).data("id");
    const sku = $(this).data("sku");
    const name = $(this).data("name");
    const displayCase = $(this).data("display-case");
    const column = $(this).data("column");
    const row = $(this).data("row");

    $("#edit-product-id").val(id);
    $("#edit-sku").val(sku);
    $("#edit-name").val(name);
    $("#edit-display-case").val(displayCase);
    $("#edit-column").val(column);
    $("#edit-row").val(row);

    $("#editProductModal").modal("show");
  });

  // Update product
  $("#update-product-btn").on("click", function () {
    const id = $("#edit-product-id").val();
    const sku = $("#edit-sku").val().trim();
    const name = $("#edit-name").val().trim();
    const originalSku = $(`.edit-product[data-id="${id}"]`).data("sku");
    const displayCase = $("#edit-display-case").val().trim();
    const column = $("#edit-column").val();
    const row = $("#edit-row").val();

    if (!sku || !name || !displayCase || !column || !row) {
      alert("Por favor, complete todos los campos.");
      return;
    }

    // Only check for SKU uniqueness if the SKU has changed
    if (sku.toUpperCase() !== originalSku) {
      checkSkuExists(sku.toUpperCase(), function (exists) {
        if (exists) {
          alert("El SKU ya existe. Por favor, utilice un SKU único.");
          return;
        }

        updateProductRequest(id, sku, name, displayCase, column, row);
      });
    } else {
      updateProductRequest(id, sku, name, displayCase, column, row);
    }
  });

  // Function to send update product request
  function updateProductRequest(id, sku, name, displayCase, column, row) {
    $.ajax({
      url: `/api/products/${id}`,
      type: "PUT",
      contentType: "application/json",
      data: JSON.stringify({
        sku: sku,
        name: name,
        display_case: displayCase,
        column: column,
        row: row,
      }),
      success: function (response) {
        if (response.success) {
          // Close modal
          $("#editProductModal").modal("hide");

          // Reload products
          loadProducts(currentPage, itemsPerPage, currentSearch);
        }
      },
      error: function (xhr) {
        const response = xhr.responseJSON;
        alert(response.message || "Error al actualizar el producto.");
      },
    });
  }

  // Delete product - show confirmation
  $(document).on("click", ".delete-product", function () {
    const id = $(this).data("id");
    const sku = $(this).data("sku");

    $("#delete-product-id").val(id);
    $("#delete-sku").text(sku);

    $("#deleteConfirmModal").modal("show");
  });

  // Confirm delete product
  $("#confirm-delete-btn").on("click", function () {
    const id = $("#delete-product-id").val();

    $.ajax({
      url: `/api/products/${id}`,
      type: "DELETE",
      success: function (response) {
        if (response.success) {
          // Close modal
          $("#deleteConfirmModal").modal("hide");

          // Reload products
          loadProducts(currentPage, itemsPerPage, currentSearch);
        }
      },
      error: function () {
        alert("Error al eliminar el producto.");
      },
    });
  });

  // Upload CSV
  $("#upload-csv-btn").on("click", function () {
    const fileInput = $("#csv-file")[0];

    if (!fileInput.files || fileInput.files.length === 0) {
      alert("Por favor, seleccione un archivo CSV.");
      return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    $.ajax({
      url: "/upload-csv",
      type: "POST",
      data: formData,
      processData: false,
      contentType: false,
      success: function (response) {
        // Display results
        $("#csv-results-message").text(response.message);

        if (response.errors && response.errors.length > 0) {
          // Display errors
          $("#csv-errors-list").empty();
          response.errors.forEach(function (error) {
            $("#csv-errors-list").append(`<li>${error}</li>`);
          });
          $("#csv-errors-container").removeClass("d-none");
        } else {
          $("#csv-errors-container").addClass("d-none");
        }

        $("#csv-upload-results").removeClass("d-none");

        // Reload products
        loadProducts(currentPage, itemsPerPage, currentSearch);
      },
      error: function (xhr) {
        const response = xhr.responseJSON;
        alert(response.message || "Error al cargar el archivo CSV.");
      },
    });
  });

  // Reset modals on close
  $("#addProductModal").on("hidden.bs.modal", function () {
    $("#add-product-form")[0].reset();
  });

  $("#uploadCsvModal").on("hidden.bs.modal", function () {
    $("#upload-csv-form")[0].reset();
    $("#csv-upload-results").addClass("d-none");
  });
});

// Function to load products with pagination and search
function loadProducts(page, perPage, search) {
  $.ajax({
    url: "/api/products",
    type: "GET",
    data: {
      page: page,
      per_page: perPage,
      search: search
    },
    success: function (response) {
      const tableBody = $("#products-table-body");
      tableBody.empty();
      
      const products = response.products;
      const totalProducts = response.total;
      const totalPages = response.pages;

      if (products.length === 0) {
        if (search) {
          $("#no-products").text("No se encontraron productos que coincidan con la búsqueda.").removeClass("d-none");
        } else {
          $("#no-products").text("No hay productos registrados. Agregue un nuevo producto o cargue un archivo CSV.").removeClass("d-none");
        }
        // Ocultar paginación
        $("#pagination-info").parent().parent().addClass("d-none");
        return;
      }

      $("#no-products").addClass("d-none");
      $("#pagination-info").parent().parent().removeClass("d-none");

      // Actualizar información de paginación
      const start = (page - 1) * perPage + 1;
      const end = Math.min(start + products.length - 1, totalProducts);
      $("#showing-start").text(start);
      $("#showing-end").text(end);
      $("#total-products").text(totalProducts);

      // Generar filas de la tabla
      products.forEach(function (product) {
        tableBody.append(`
          <tr>
            <td>${product.sku}</td>
            <td>${product.name}</td>
            <td>${product.display_case}</td>
            <td>${product.row}</td>
            <td>${product.column}</td>
            <td>
              <button class="btn btn-sm btn-primary edit-product"
                data-id="${product.id}"
                data-sku="${product.sku}"
                data-name="${product.name}"
                data-display-case="${product.display_case}"
                data-column="${product.column}"
                data-row="${product.row}">
                <i class="bi bi-pencil"></i>
              </button>
              <button class="btn btn-sm btn-danger delete-product"
                data-id="${product.id}"
                data-sku="${product.sku}">
                <i class="bi bi-trash"></i>
              </button>
            </td>
          </tr>
        `);
      });

      // Generar controles de paginación
      generatePagination(page, totalPages, search);
    },
    error: function () {
      alert("Error al cargar los productos.");
    },
  });
}

// Función para generar los controles de paginación
function generatePagination(currentPage, totalPages, search) {
  const paginationControls = $("#pagination-controls");
  paginationControls.empty();

  // No mostrar paginación si solo hay una página
  if (totalPages <= 1) {
    return;
  }

  // Botón "Anterior"
  paginationControls.append(`
    <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
      <a class="page-link" href="#" data-page="${currentPage - 1}" aria-label="Anterior">
        <span aria-hidden="true">&laquo;</span>
      </a>
    </li>
  `);

  // Determinar qué páginas mostrar
  let startPage = Math.max(1, currentPage - 2);
  let endPage = Math.min(totalPages, startPage + 4);
  
  // Ajustar si estamos cerca del final
  if (endPage - startPage < 4) {
    startPage = Math.max(1, endPage - 4);
  }

  // Generar botones de página
  for (let i = startPage; i <= endPage; i++) {
    paginationControls.append(`
      <li class="page-item ${i === currentPage ? 'active' : ''}">
        <a class="page-link" href="#" data-page="${i}">${i}</a>
      </li>
    `);
  }

  // Botón "Siguiente"
  paginationControls.append(`
    <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
      <a class="page-link" href="#" data-page="${currentPage + 1}" aria-label="Siguiente">
        <span aria-hidden="true">&raquo;</span>
      </a>
    </li>
  `);

  // Manejar clics en los controles de paginación
  $(".page-link").on("click", function(e) {
    e.preventDefault();
    const page = $(this).data("page");
    
    // Verificar que la página sea válida
    if (page >= 1 && page <= totalPages && page !== currentPage) {
      loadProducts(page, itemsPerPage, search);
      currentPage = page;
    }
  });
}
