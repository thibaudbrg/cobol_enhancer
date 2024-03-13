000010 IDENTIFICATION DIVISION.                                                 
000020 PROGRAM-ID. READCARD.                                                    
000030 AUTHOR.TATA CONSULTANCY SERVICES.                                        
000040 DATE-COMPILED.FEB 2006.                                                  
************************************************************************        
000060*THIS PROGRAM READS THE INSTREAM DATA AND WRITES TO SYSOUT.               
************************************************************************        
000080 ENVIRONMENT DIVISION.                                                    
************************************************************************
000100*THE FOLLOWING LINES OF CODE  COMMENTED AS THIS IS NOT REQUIRED BY   
000110*THE PROGRAM FUNCTIONALITY.
************************************************************************
TOFAN8*CONFIGURATION SECTION.
TOFAN8*SOURCE-COMPUTER. IBM-390.
TOFAN8*OBJECT-COMPUTER.
TOFAN8*    PROGRAM COLLATING SEQUENCE EBC.
TOFAN8*SPECIAL-NAMES.
TOFAN8*    ALPHABET EBC IS EBCDIC.
000190 INPUT-OUTPUT SECTION.                                                    
000200 FILE-CONTROL.                                                            
000210     SELECT CARD ASSIGN TO CARDIN                                         
000220     ORGANIZATION IS LINE SEQUENTIAL                                      
000230     ACCESS IS SEQUENTIAL                                                 
000240     FILE STATUS IS F-KEY1.                                               
000250                                                                          
000260     SELECT COUT ASSIGN TO  READOUT                                       
000270     ORGANIZATION IS LINE SEQUENTIAL                                      
000280     ACCESS IS SEQUENTIAL                                                 
000290     FILE STATUS IS F-KEY2.                                               
000300                                                                          
000310 DATA DIVISION.                                                           
000320 FILE SECTION.                                                            
000330 FD COUT.                                                                 
000340 01 OUT-REC          PIC X(133).                                          
000350                                                                          
000360 FD CARD.                                                                 
000370 01 INP-REC          PIC X(80).                                           
000380 WORKING-STORAGE SECTION.                                                 
000390 77  CMS-IDENTIFICATION PIC X(8) VALUE 'WEADCARD'.                        
000400 77  CMS-ID-VALUE PIC X(44)   VALUE                                       
000410         'CMS-ID=17/02/06/15:58:32/GWDR/TOFRS8  /V0   '.                  
000420 77  WS-OPEN-FLAG      PIC X(1) VALUE IS 'N'.                             
************************************************************************        
000440*         RECORD FORMAT IN THE OUTPUT FILE                                
************************************************************************        
000460                                                                          
000470 01  LINE1.                                                               
000480     05  FILLER        PIC X(48) VALUE IS                                 
000490-       '****************** DEBUT DES CARTES PARAMETRES '.                
000500     05  FILLER       PIC X(32) VALUE IS ALL '*'.                         
000510     05  FILLER       PIC X(53) VALUE IS SPACES.                          
000520 01  LINE2.                                                               
000530     05  FILLER        PIC X(40) VALUE IS                                 
000540-       '1...5...10....5...20....5...30....5...40'.                       
000550     05  FILLER        PIC X(40) VALUE IS                                 
000560-       '....5...50....5...60....5...70....5...80'.                       
000570     05  FILLER       PIC X(53) VALUE IS SPACES.                          
000580 01  LINE3.                                                               
000590     05  FILLER        PIC X(46) VALUE IS                                 
000600-       '****************** FIN DES CARTES PARAMETRES '.                  
000610     05  FILLER       PIC X(34) VALUE IS ALL '*'.                         
000620     05  FILLER       PIC X(53) VALUE IS SPACES.                          
000630 01  PARAMETER-LINE.                                                      
000640     05  PARAMETERS    PIC X(80).                                         
000650     05  FILLER       PIC X(53) VALUE IS SPACES.                          
000660 77  F-KEY1     PIC X(2).                                                 
000670 77  F-KEY2     PIC X(2).                                                 
000680 LINKAGE SECTION.                                                         
000690  01  LK-CARTE  PIC X(80).                                                
000700 PROCEDURE DIVISION USING LK-CARTE.                                       
000710 MAIN-PARA.                                                               
************************************************************************        
000730*         CHECKS IF THE FILE IS OPEN                                      
************************************************************************        
000750      IF WS-OPEN-FLAG = 'Y'                                               
000760          GO TO READ-PARA                                                 
000770      END-IF.                                                             
************************************************************************        
000790*     ALLOCATES READOUT TO SYSOUT USING BPXWDYN                           
************************************************************************        
000810      OPEN INPUT CARD.                                                    
000820      MOVE 'Y' TO WS-OPEN-FLAG.                                           
000830      OPEN OUTPUT COUT.                                                   
000840      PERFORM INIT-PARA.                                                  
000850      PERFORM READ-PARA.                                                  
000860 INIT-PARA.                                                               
************************************************************************        
000880*         WRITES FIRST AND SECOND LINE TO SYSOUT                          
************************************************************************        
000900      WRITE OUT-REC FROM LINE1                                            
000910      WRITE OUT-REC FROM LINE2.                                           
000920 READ-PARA.                                                               
************************************************************************        
000940*         READS INSTREAM DATA AND WRITES TO SYSOUT                        
************************************************************************        
000960      READ CARD INTO PARAMETERS AT END GO TO CLOSE-PARA.                  
000970      MOVE PARAMETERS TO  LK-CARTE.                            
000980      WRITE OUT-REC FROM PARAMETER-LINE                                
000990      PERFORM GOBACK-PARA.                                                
001000 CLOSE-PARA.                                                              
************************************************************************        
001020*         WRITES LAST LINE  TO SYSOUT                                     
************************************************************************        
001040      MOVE '/*' TO LK-CARTE                                               
001050      WRITE OUT-REC FROM LINE3.                                           
001060      CLOSE CARD.                                                         
001070      CLOSE COUT.                                                         
001080 GOBACK-PARA.                                                             
001090      GOBACK.                                                             
