// STM32F2 FSMC support
//
// Copyright (C) 2019  Kevin O'Connor <kevin@koconnor.net>
//
// This file may be distributed under the terms of the GNU GPLv3 license.

#include "board/internal.h" // GPIO
#include "stm32f2xx_fsmc.h"

#define RCC_AHB3Periph_FSMC               ((uint32_t)0x00000001)

#define FSMC_FUNCTION  GPIO_FUNCTION(12) // Alternative function mapping number

// TODO: TFTLCD_DRIVER_SPEED configurable
#define TFTLCD_DRIVER_SPEED 0x10

void enable_i8080_fsmc(uint32_t cs_pin, uint32_t rs_pin)
{
    FSMC_NORSRAMInitTypeDef  FSMC_NORSRAMInitStructure;
    FSMC_NORSRAMTimingInitTypeDef  readWriteTiming,writeTiming;

    // Configure STM32F2 FSMC data pins ; D0 - D15
    gpio_peripheral(GPIO('D', 0), FSMC_FUNCTION, 0);
    gpio_peripheral(GPIO('D', 1), FSMC_FUNCTION, 0);
    gpio_peripheral(GPIO('D', 8), FSMC_FUNCTION, 0);
    gpio_peripheral(GPIO('D', 9), FSMC_FUNCTION, 0);
    gpio_peripheral(GPIO('D', 10), FSMC_FUNCTION, 0);
    gpio_peripheral(GPIO('D', 14), FSMC_FUNCTION, 0);
    gpio_peripheral(GPIO('D', 15), FSMC_FUNCTION, 0);
    gpio_peripheral(GPIO('E', 7), FSMC_FUNCTION, 0);
    gpio_peripheral(GPIO('E', 8), FSMC_FUNCTION, 0);
    gpio_peripheral(GPIO('E', 9), FSMC_FUNCTION, 0);
    gpio_peripheral(GPIO('E', 10), FSMC_FUNCTION, 0);
    gpio_peripheral(GPIO('E', 11), FSMC_FUNCTION, 0);
    gpio_peripheral(GPIO('E', 12), FSMC_FUNCTION, 0);
    gpio_peripheral(GPIO('E', 13), FSMC_FUNCTION, 0);
    gpio_peripheral(GPIO('E', 14), FSMC_FUNCTION, 0);
    gpio_peripheral(GPIO('E', 15), FSMC_FUNCTION, 0);

    // Confiure STM32F2 FSMC control pins
    // FSMC_NOE :LCD-RD
    gpio_peripheral(GPIO('D', 4), FSMC_FUNCTION, 0);
    // FSMC_NWE :LCD-WR
    gpio_peripheral(GPIO('D', 5), FSMC_FUNCTION, 0);
    // FSMC_A23 :LCD-RS
    //    gpio_peripheral(GPIO('E', 2), FSMC_FUNCTION, 0);
    gpio_peripheral(rs_pin, FSMC_FUNCTION, 0);
    // FSMC_NEx :LCD-CS
    //    gpio_peripheral(GPIO('D', 7), FSMC_FUNCTION, 0);
    gpio_peripheral(cs_pin, FSMC_FUNCTION, 0);

    // start FSMC clock
    RCC->AHB3ENR |= RCC_AHB3Periph_FSMC;
  
    //#define FSMC_AccessMode_A                        ((uint32_t)0x00000000)

    readWriteTiming.FSMC_AddressSetupTime = 0x01;
    // Address setup time (ADDSET) is 2 HCLK 1 / 36M = 27ns
    readWriteTiming.FSMC_AddressHoldTime = 0x00;
    readWriteTiming.FSMC_DataSetupTime = 0x0f;
    readWriteTiming.FSMC_BusTurnAroundDuration = 0x00;
    readWriteTiming.FSMC_CLKDivision = 0x00;
    readWriteTiming.FSMC_DataLatency = 0x00;
    readWriteTiming.FSMC_AccessMode = FSMC_AccessMode_A;
    // Mode A

    writeTiming.FSMC_AddressSetupTime = 0x00;
    // Address setup time (ADDSET) is 1 HCLK
    writeTiming.FSMC_AddressHoldTime = 0x00;
    writeTiming.FSMC_DataSetupTime = TFTLCD_DRIVER_SPEED;
    // Data save time
    writeTiming.FSMC_BusTurnAroundDuration = 0x00;
    writeTiming.FSMC_CLKDivision = 0x00;
    writeTiming.FSMC_DataLatency = 0x00;
    writeTiming.FSMC_AccessMode = FSMC_AccessMode_A;
    // Mode A

    FSMC_NORSRAMInitStructure.FSMC_Bank = FSMC_Bank1_NORSRAM1;
    // Select the address of the external storage area
    FSMC_NORSRAMInitStructure.FSMC_DataAddressMux = FSMC_DataAddressMux_Disable;
    // Configure whether the data and address lines are multiplexed
    FSMC_NORSRAMInitStructure.FSMC_MemoryType = FSMC_MemoryType_NOR;
    // Configure the type of external storage
    FSMC_NORSRAMInitStructure.FSMC_MemoryDataWidth = FSMC_MemoryDataWidth_16b;
    // Set the data width of the FSMC interface

    FSMC_NORSRAMInitStructure.FSMC_BurstAccessMode = FSMC_BurstAccessMode_Disable;
    // Configure access mode
    FSMC_NORSRAMInitStructure.FSMC_WaitSignalPolarity = FSMC_WaitSignalPolarity_Low;
    // Configure the polarity of the wait signal
    FSMC_NORSRAMInitStructure.FSMC_WrapMode = FSMC_WrapMode_Disable;
    // Configure whether to use non-alignment
    FSMC_NORSRAMInitStructure.FSMC_AsynchronousWait = FSMC_AsynchronousWait_Disable;
    FSMC_NORSRAMInitStructure.FSMC_WaitSignalActive = FSMC_WaitSignalActive_BeforeWaitState;
    // Configure when to wait for signals
    FSMC_NORSRAMInitStructure.FSMC_WaitSignal = FSMC_WaitSignal_Disable;
    // Configure whether to use wait signals
    FSMC_NORSRAMInitStructure.FSMC_WriteBurst = FSMC_WriteBurst_Disable;
    // Configure whether to allow burst writes

    FSMC_NORSRAMInitStructure.FSMC_WriteOperation = FSMC_WriteOperation_Enable;
    // Configuration write operation enabled
    FSMC_NORSRAMInitStructure.FSMC_ExtendedMode = FSMC_ExtendedMode_Enable;
    // Configure whether to use extended mode

    FSMC_NORSRAMInitStructure.FSMC_ReadWriteTimingStruct = &readWriteTiming;
    // Read timing
    FSMC_NORSRAMInitStructure.FSMC_WriteTimingStruct = &writeTiming;
    // Write timing

    FSMC_NORSRAMInit(&FSMC_NORSRAMInitStructure);
    // Enable FSMC Bank1_SRAM Bank
    FSMC_NORSRAMCmd(FSMC_Bank1_NORSRAM1, ENABLE);
}

typedef struct
{
    volatile uint16_t LCD_REG;
    volatile uint16_t LCD_RAM;
} LCD_TypeDef;

// TODO: derive LCD_BASE from RS pin
#define LCD_BASE        ((uint32_t)(0x60000000 | 0x00FFFFFE))  // 1111 1111 1111 1111 1111 1110
#define LCD             ((LCD_TypeDef *) LCD_BASE)

//#define LCD_WR_REG(regval) do{ LCD->LCD_REG = regval; }while(0)
//#define LCD_WR_DATA(data)  do{ LCD->LCD_RAM = data; }while(0)

void
i8080_fsmc_wr_reg(uint16_t cmd)
{
    //    LCD_WR_REG(cmd);
     LCD->LCD_REG = cmd;
}

void
i8080_fsmc_wr_data(uint16_t data)
{
    //    LCD_WR_DATA(data);
    LCD->LCD_RAM = data;
}

/* uint16_t LCD_RD_DATA(void) */
/* { */
/*     volatile uint16_t ram; */
/*     ram = LCD->LCD_RAM; */
/*     return ram; */
/* } */

uint16_t
i8080_fsmc_rd_data(void)
{
    //    return LCD_RD_DATA;
    volatile uint16_t ram;
    ram = LCD->LCD_RAM;
    return ram;
}

void i8080_fsmc_rd_multi_data(uint16_t cmd, uint16_t *pdata, uint32_t cnt)
{
    i8080_fsmc_wr_reg(cmd);
    while(cnt--) {
	*pdata = i8080_fsmc_rd_data();
	pdata++;
    }
}

